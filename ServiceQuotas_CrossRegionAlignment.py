import boto3
from time import sleep

# https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/service-quotas.html#id22


def list_services(region='us-east-1'):
    client = boto3.client('service-quotas', region_name=region)
    response = client.list_services(
        MaxResults=100
    )
    service_list = response['Services']
    while 'NextToken' in response:
        response = client.list_services(
            MaxResults=100,
            NextToken=response['NextToken']
        )
        service_list = service_list + response['Services']
    return service_list


def list_service_quotas(servicename, region='us-east-1'):
    client = boto3.client('service-quotas', region_name=region)
    response = client.list_service_quotas(
        ServiceCode=servicename,
        MaxResults=100
    )
    quotas = response['Quotas']
    while 'NextToken' in response:
        response = client.list_service_quotas(
            ServiceCode=servicename,
            MaxResults=100,
            NextToken=response['NextToken']
        )
        quotas = quotas + response['Quotas']
    return quotas


def request_service_quota_increase(servicecode, quotacode, desiredvalue,
                                   region='us-east-1'):
    service_quotas_client = boto3.client('service-quotas', region_name=region)
    response = service_quotas_client.request_service_quota_increase(
        ServiceCode=servicecode,
        QuotaCode=quotacode,
        DesiredValue=desiredvalue
    )
    return response


if __name__ == '__main__':
    src_region = 'us-east-1'
    dst_region = 'us-east-2'
    # Get services list from origin region
    services = list_services(region=src_region)
    for service in services:
        # ignore service if not exist in destination region
        if service not in list_services(dst_region):
            continue

        # get service quotas in origin region
        serviceQuotas = list_service_quotas(service['ServiceCode'], region=src_region)
        # get service quotas in destination region
        dst_region_serviceQuotas = list_service_quotas(service['ServiceCode'], region=dst_region)
        # check if quotas exist for service
        if len(serviceQuotas) > 0:
            for q in serviceQuotas:
                # check if if service quota is adjustable
                if q['Adjustable'] is False:
                    continue
                # check if there is a gap between service quotas for the regions
                for q2 in dst_region_serviceQuotas:
                    if q['QuotaCode'] == q2['QuotaCode'] \
                            and q['Value'] != q2['Value']:

                        print(q['ServiceCode'], q['QuotaName'], q['Value'],
                              q2['Value'],
                              q['GlobalQuota'], q['QuotaArn'], q['QuotaCode'])

                        # we don't want to throttle aws api
                        sleep(2)
                        try:
                            # put request for a service limit on destination region
                            request_service_quota_increase(q['ServiceCode'],
                                                           q['QuotaCode'],
                                                           q['Value'],
                                                           region=dst_region)
                        except Exception as e:
                            print(e)
