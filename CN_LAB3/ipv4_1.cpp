#include "sysInclude.h"
#include <stdio.h>
#include <malloc.h>
extern void ip_DiscardPkt(char *pBuffer, int type);

extern void ip_SendtoLower(char *pBuffer, int length);

extern void ip_SendtoUp(char *pBuffer, int length);

extern unsigned int getIpv4Address();

// implemented by students

int stud_ip_recv(char *pBuffer, unsigned short length)
{
    int version = pBuffer[0] >> 4;//提取version
    int ihl = pBuffer[0] & 0xf;//提取ihl
    short ttl = (unsigned short)pBuffer[8];//提取ttl
    short checksum = ntohs(*(unsigned short *)(pBuffer + 10));//提取checksum
    int destination = ntohl(*(unsigned int *)(pBuffer + 16));//提取destination
    //version错误
    if (version != 4)
    {
        ip_DiscardPkt(pBuffer, STUD_IP_TEST_VERSION_ERROR);
        return 1;
    }
    //ihl错误
    if (ihl < 5 || ihl > 12)
    {
        ip_DiscardPkt(pBuffer, STUD_IP_TEST_HEADLEN_ERROR);
        return 1;
    }
    //ttl错误
    if (ttl <= 0)
    {
        ip_DiscardPkt(pBuffer, STUD_IP_TEST_TTL_ERROR);
        return 1;
    }
    //destination错误
    if (destination != getIpv4Address() && destination != 0xffff)
    {
        ip_DiscardPkt(pBuffer, STUD_IP_TEST_DESTINATION_ERROR);
        return 1;
    }
    //计算检验和
    unsigned long sum = 0;
    unsigned long temp = 0;
    int i;
    for (i = 0; i < ihl * 2; i++)
    {
        temp += (unsigned char)pBuffer[i * 2] << 8;
        temp += (unsigned char)pBuffer[i * 2 + 1];
        sum += temp;
        temp = 0;
    }
    unsigned short l_word = sum & 0xffff;
    unsigned short h_word = sum >> 16;
    //检验和错误
    if (l_word + h_word != 0xffff)
    {
        ip_DiscardPkt(pBuffer, STUD_IP_TEST_CHECKSUM_ERROR);
        return 1;
    }
    //全部正确
    ip_SendtoUp(pBuffer, length);
    return 0;
}

int stud_ip_Upsend(char *pBuffer, unsigned short len, unsigned int srcAddr,
                   unsigned int dstAddr, byte protocol, byte ttl)
{
    short ip_length = len + 20;//报文长度
    char *buffer = (char *)malloc(ip_length * sizeof(char));//分配报文空间
    memset(buffer, 0, ip_length);//初始化
    buffer[0] = 0x45;//version和ihl
    buffer[8] = ttl;//ttl
    buffer[9] = protocol;//协议
    unsigned short network_length = htons(ip_length);//网络字节转换
    memcpy(buffer + 2, &network_length, 2);//设置网络字节序
    unsigned int src = htonl(srcAddr);//网络字节转换
    unsigned int dst = htonl(dstAddr);//网络字节转换
    //设置源目的地址
    memcpy(buffer + 12, &src, 4);
    memcpy(buffer + 16, &dst, 4);
    //计算检验和
    unsigned long sum = 0;
    unsigned long temp = 0;
    int i;
    for (i = 0; i < 20; i += 2)
    {
        temp += (unsigned char)buffer[i] << 8;
        temp += (unsigned char)buffer[i + 1];
        sum += temp;
        temp = 0;
    }
    unsigned short l_word = sum & 0xffff;
    unsigned short h_word = sum >> 16;
    unsigned short checksum = l_word + h_word;
    checksum = ~checksum;
    unsigned short header_checksum = htons(checksum);
    memcpy(buffer + 10, &header_checksum, 2);//设置检验和
    memcpy(buffer + 20, pBuffer, len);//设置报文长度
    ip_SendtoLower(buffer, len + 20);//向底层发送
    return 0;
}