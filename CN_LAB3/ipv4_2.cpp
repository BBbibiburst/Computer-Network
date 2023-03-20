#include "sysInclude.h"
#include <stdio.h>
#include <vector>

// system support
extern void fwd_LocalRcv(char *pBuffer, int length);

extern void fwd_SendtoLower(char *pBuffer, int length, unsigned int nexthop);

extern void fwd_DiscardPkt(char *pBuffer, int type);

extern unsigned int getIpv4Address();

// implemented by students

std::vector<stud_route_msg> route;

void stud_Route_Init()
{
	route.clear()
	return;
}

void stud_route_add(stud_route_msg *proute)
{

	stud_route_msg temp;
	unsigned int dest = ntohl(proute->dest);
	unsigned int masklen = ntohl(proute->masklen);
	unsigned int nexthop = ntohl(proute->nexthop);
	temp.dest = dest;
	temp.masklen = masklen;
	temp.nexthop = nexthop;
	route.push_back(temp);
	return;
}

int stud_fwd_deal(char *pBuffer, int length)
{
	int version = pBuffer[0] >> 4;
	int head_length = pBuffer[0] & 0xf;
	short ttl = (unsigned short)pBuffer[8];
	short checksum = ntohs(*(unsigned short *)(pBuffer + 10));
	int destination = ntohl(*(unsigned int *)(pBuffer + 16));
	if (ttl <= 0)
	{
		fwd_DiscardPkt(pBuffer, STUD_FORWARD_TEST_TTLERROR);
		return 1;
	}
	if (destination == getIpv4Address())
	{
		fwd_LocalRcv(pBuffer, length);
		return 0;
	}
	stud_route_msg *ans_route = NULL;
	int temp_dest = destination;
	for (int i = 0; i < route.size(); i++)
	{
		unsigned int temp_sub_net = route[i].dest & ((1 << 31) >> (route[i].masklen - 1));

		if (temp_sub_net == temp_dest)
		{
			ans_route = &route[i];
			break;
		}
	}

	if (!ans_route)
	{
		fwd_DiscardPkt(pBuffer, STUD_FORWARD_TEST_NOROUTE);
		return 1;
	}
	else
	{
		char *buffer = new char[length];
		memcpy(buffer, pBuffer, length);
		buffer[8] = ttl - 1;
		memset(buffer + 10, 0, 2);
		unsigned long sum = 0;
		unsigned long temp = 0;

		for (int i = 0; i < head_length * 2; i++)
		{
			temp += (unsigned char)buffer[i * 2] << 8;
			temp += (unsigned char)buffer[i * 2 + 1];
			sum += temp;
			temp = 0;
		}
		unsigned short l_word = sum & 0xffff;
		unsigned short h_word = sum >> 16;
		unsigned short checksum = l_word + h_word;
		checksum = ~checksum;
		unsigned short header_checksum = htons(checksum);
		memcpy(buffer + 10, &header_checksum, 2);
		fwd_SendtoLower(buffer, length, ans_route->nexthop);
	}
	return 0;
}