# -*- coding: utf-8 -*-
import json
import os
import urllib
import urllib.parse

from helpers.csp_helper import append_csp_data, default_csp_result_object
from helpers.data_helper import append_domain_entry,\
    append_domain_entry_with_key, has_domain_entry_with_key
from helpers.http_header_helper import append_data_from_response_headers
from helpers.sri_helper import append_sri_data

def get_data_from_sitespeed(filename, org_domain):
    """
    Extracts data from a HAR (HTTP Archive) file generated by SiteSpeed and
    updates a result dictionary.

    This function reads a HAR file and iterates over the entries in the log.
    For each entry, it extracts information such as the request URL,
    scheme, HTTP version, and server IP address. It also appends data 
    from the response headers and MIME types.
    The extracted information is then added to the result dictionary 
    under the appropriate categories.

    Parameters:
    filename (str): The name of the HAR file to be read.
    org_domain (str): The original domain for which the HAR file was generated.

    Returns:
    dict: The result dictionary updated with the extracted information.
          The dictionary also includes a 'visits' key which is set to
          1 to indicate that the function has been called once for the given HAR file.
    """
    result = {
        'visits': 0,
        org_domain: default_csp_result_object(True)
    }

    if filename == '':
        return result

    if not os.path.exists(filename):
        return result

    # Fix for content having unallowed chars
    with open(filename, encoding='utf-8') as json_input_file:
        har_data = json.load(json_input_file)

        if 'log' in har_data:
            har_data = har_data['log']

        # return zero visits if no entries
        if len(har_data["entries"]) == 0:
            return result

        for entry in har_data["entries"]:
            req = entry['request']
            res = entry['response']
            req_url = req['url']

            o = urllib.parse.urlparse(req_url)
            req_domain = o.hostname

            if req_domain not in result:
                result[req_domain] = default_csp_result_object(False)

            append_domain_entry(req_domain, 'schemes', o.scheme.upper(), result)
            append_domain_entry(req_domain, 'urls', req_url, result)

            scheme = f'{o.scheme.lower()}:'
            if not has_domain_entry_with_key(
                    org_domain,
                    'csp-findings',
                    'scheme-sources',
                    scheme, result) and scheme != 'http:':
                append_domain_entry_with_key(
                    org_domain,
                    'csp-findings',
                    'scheme-sources',
                    scheme,
                    result)

            if 'httpVersion' in req and req['httpVersion'] != '':
                http_version = req['httpVersion'].replace('h2', 'HTTP/2')
                http_version = http_version.replace('h3', 'HTTP/3')
                http_version = http_version.upper()
                append_domain_entry(req_domain, 'protocols', http_version, result)

            if 'httpVersion' in res and res['httpVersion'] != '':
                http_version = res['httpVersion'].replace('h2', 'HTTP/2')
                http_version = http_version.replace('h3', 'HTTP/3')
                http_version = http_version.upper()
                append_domain_entry(req_domain, 'protocols', http_version, result)

            if 'serverIPAddress' in entry:
                if ':' in entry['serverIPAddress']:
                    append_domain_entry(req_domain, 'ip-versions', 'IPv6', result)
                else:
                    append_domain_entry(req_domain, 'ip-versions', 'IPv4', result)

            append_data_from_response_headers(
                res['headers'],
                req_url,
                org_domain,
                req_domain,
                result)

            append_csp_data(req_url, req_domain, res, org_domain, result)
            append_sri_data(req_domain, res, result)

    result['visits'] = 1
    return result
