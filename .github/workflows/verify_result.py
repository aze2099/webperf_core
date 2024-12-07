# -*- coding: utf-8 -*-
from pathlib import Path
import os
import os.path
import ssl
import sys
import getopt
import json
import shutil
import re
import requests

# DEFAULTS
REQUEST_TIMEOUT = 60
USERAGENT = 'Mozilla/5.0 (compatible; Windows NT 10.0; Win64; x64) ' \
     'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.96 Safari/537.36 Edg/88.0.705.56'

def get_http_content(url, allow_redirects=False, use_text_instead_of_content=True):
    """
    Retrieves the content of the specified URL and caches it.

    This function first checks if the content is already cached. If it is, 
    the cached content is returned. If not, a GET request is sent to the 
    URL. The content of the response is then cached and returned.

    In case of SSL or connection errors, the function retries the request 
    using HTTPS if the original URL used HTTP. If the request times out, 
    an error message is printed.

    Args:
        url (str): The URL to retrieve the content from.
        allow_redirects (bool, optional): Whether to follow redirects. 
                                           Defaults to False.
        use_text_instead_of_content (bool, optional): Whether to retrieve 
                                                      the response content 
                                                      as text (True) or 
                                                      binary (False). 
                                                      Defaults to True.

    Returns:
        str or bytes: The content of the URL.
    """
    try:
        headers = {'user-agent': USERAGENT}
        response = requests.get(url, allow_redirects=allow_redirects,
                         headers=headers, timeout=REQUEST_TIMEOUT*2)

        if use_text_instead_of_content:
            content = response.text
        else:
            content = response.content

        return content
    except ssl.CertificateError as error:
        print(f'Info: Certificate error. {error.reason}')
    except requests.exceptions.SSLError as error:
        if 'http://' in url:  # trying the same URL over SSL/TLS
            print('Info: Trying SSL before giving up.')
            return get_http_content(url.replace('http://', 'https://'))
        print(f'Info: SSLError. {error}')
    except requests.exceptions.ConnectionError as error:
        if 'http://' in url:  # trying the same URL over SSL/TLS
            print('Connection error! Info: Trying SSL before giving up.')
            return get_http_content(url.replace('http://', 'https://'))
        print(
            'Connection error! Unfortunately the request for URL '
            f'"{url}" failed.\nMessage:\n{sys.exc_info()[0]}')
    except requests.exceptions.MissingSchema as error:
        print(
            'Connection error! Missing Schema for '
            f'"{url}"')
    except requests.exceptions.TooManyRedirects as error:
        print(
            'Connection error! Too many redirects for '
            f'"{url}"')
    except requests.exceptions.InvalidURL:
        print(
            'Connection error! Invalid url '
            f'"{url}"')
    except TimeoutError:
        print(
            'Error! Unfortunately the request for URL '
            f'"{url}" timed out.'
            f'The timeout is set to {REQUEST_TIMEOUT} seconds.\nMessage:\n{sys.exc_info()[0]}')
    return ''


def prepare_config_file(sample_filename, filename, arguments):
    """
    Prepares a configuration file based on a sample file and a set of arguments.

    This function performs the following steps:
    1. Checks if the sample file exists. If not, it returns False.
    2. If the target file already exists, it removes it.
    3. Copies the sample file to the target file location.
    4. Opens the new file and reads its contents.
    5. Iterates over each line in the file and each argument in the arguments list.
    6. For each argument, it finds the name and value and constructs a new line with these values.
    7. Writes the modified lines back to the file.
    8. Prints the contents of the new file for debugging purposes.

    Args:
        sample_filename (str): The path to the sample configuration file.
        filename (str): The path where the new configuration file should be created.
        arguments (list): A list of strings where each string is
          an argument in the format 'name=value'.

    Returns:
        bool: True if the operation was successful, False otherwise.
    """

    if not os.path.exists(sample_filename):
        print('no sample file exist at:', sample_filename)
        return False

    if sample_filename != filename and os.path.exists(filename):
        print(filename + ' file already exist, removing it')
        os.remove(filename)

    if sample_filename != filename:
        shutil.copyfile(sample_filename, filename)

    if not os.path.exists(filename):
        print('no file exist')
        return False

    with open(filename, 'r', encoding="utf-8") as file:
        data = file.readlines()
        output = list('')
        for line in data:
            tmp = line
            for argument in arguments:
                index = argument.find('=')
                name = argument[:index]
                value = argument[(index + 1):]

                regex_argument = f'^{name}.*'
                if value in ('True', 'False', 'None'):
                    result_argument = f'{name} = {value}'
                else:
                    result_argument = f"{name} = '{value}'"


                tmp = re.sub(regex_argument, result_argument,
                             tmp, 0, re.MULTILINE)
            output.append(tmp)

    with open(filename, 'w', encoding="utf-8") as outfile:
        outfile.writelines(output)

    # show resulting config in output for debug reasons
    print('config.py:\n')
    print('\n'.join(output))
    return True


def make_test_comparable(input_filename):
    """
    Modifies a JSON test file to make it comparable by removing date information.

    This function performs the following steps:
    1. Opens the input file and loads the JSON data.
    2. Iterates over each test in the data. If a test contains a "date" field,
      it replaces the date with the string "removed for comparison".
    3. Writes the modified data back to the input file.

    Args:
        input_filename (str): The path to the JSON file to be modified.

    Note: This function modifies the input file in-place.
      Make sure to create a backup if you need to preserve the original data.
    """

    with open(input_filename, encoding="utf-8") as json_input_file:
        data = json.load(json_input_file)
        for test in data["tests"]:
            if "date" in test:
                test["date"] = "removed for comparison"

    with open(input_filename, 'w', encoding="utf-8") as outfile:
        json.dump(data, outfile)


def print_file_content(input_filename):
    """
    Prints the content of a file line by line.

    This function performs the following steps:
    1. Prints the name of the input file.
    2. Opens the input file in read mode.
    3. Reads the file line by line.
    4. Prints each line.

    Args:
        input_filename (str): The path to the file to be read.

    Note: This function assumes that the file exists and can be opened.
      If the file does not exist or cannot be opened, an error will occur.
    """

    print('input_filename=' + input_filename)
    with open(input_filename, 'r', encoding="utf-8") as file:
        data = file.readlines()
        for line in data:
            print(line)

def get_file_content(input_filename):
    """
    Reads the content of a file and returns it as a string.

    This function performs the following steps:
    1. Opens the input file in read mode.
    2. Reads the file line by line and stores each line in a list.
    3. Joins the list of lines into a single string with newline characters between each line.

    Args:
        input_filename (str): The path to the file to be read.

    Returns:
        str: The content of the file as a string.

    Note: This function assumes that the file exists and can be opened.
      If the file does not exist or cannot be opened, an error will occur.
    """

    with open(input_filename, 'r', encoding='utf-8', newline='') as file:
        data = file.read()
        return data

def validate_failures():
    """
    Verifies if a unhandled exception occured or not.
    If True, we print content of failures.log
    If False, we do nothing
    """
    base_directory = Path(os.path.dirname(
            os.path.realpath(__file__)) + os.path.sep).parent.parent
    filename = 'failures.log'
    filename = os.path.join(base_directory.resolve(), filename)
    if not os.path.exists(filename):
        print(f'no {filename} exists')
        return True

    print('failures happend while running test')
    print_file_content(filename)
    return True

def validate_testresult(arg): # pylint: disable=too-many-return-statements,too-many-branches,too-many-statements
    """
    Validates the test result by checking the existence and content of a specific JSON file.

    This function checks if a JSON file named 'testresult-{test_id}.json' exists
      in the same directory as this script.
    If the file exists, it checks if it has a valid test content.

    Parameters:
    arg (str): The test_id used to identify the test result file.

    Returns:
    bool: True if the test result file exists and contains valid test results, False otherwise.
    """

    base_directory = Path(os.path.dirname(
        os.path.realpath(__file__)) + os.path.sep).parent.parent
    test_id = arg
    filename = f'testresult-{test_id}.json'
    filename = os.path.join(base_directory, "data", filename)
    if not os.path.exists(filename):
        print(f"test result doesn\'t exists: {filename}")
        return False

    content = get_file_content(filename)
    # for all other test it is enough that we have a file in place for now
    if '{"tests": []}' in content:
        print('Test failed, empty test results only')
        print_file_content(filename)
        return False

    data = json.loads(content)
    if not isinstance(data, dict):
        print('Test failed, test results are not a dict')
        print_file_content(filename)
        return False

    if 'tests' not in data:
        print('Test failed, test results doesn\'t have a root element \'tests\'')
        print_file_content(filename)
        return False

    if not isinstance(data['tests'], list):
        print('Test failed, test results are not in a list under the \'tests\' element')
        print_file_content(filename)
        return False

    if len(data['tests']) == 0:
        print('Test failed, has less than 1 test results')
        print_file_content(filename)
        return False

    first_test_result = data['tests'][0]
    if 'site_id' not in first_test_result:
        print('Test failed, missing \'site_id\' field in first test result')
        print_file_content(filename)
        return False

    if 'type_of_test' not in first_test_result:
        print('Test failed, missing \'type_of_test\' field in first test result')
        print_file_content(filename)
        return False

    if 'report' not in first_test_result:
        print('Test failed, missing \'report\' field in first test result')
        print_file_content(filename)
        return False

    if 'report_sec' not in first_test_result:
        print('Test failed, missing \'report_sec\' field in first test result')
        print_file_content(filename)
        return False

    if 'report_perf' not in first_test_result:
        print('Test failed, missing \'report_perf\' field in first test result')
        print_file_content(filename)
        return False

    if 'report_a11y' not in first_test_result:
        print('Test failed, missing \'report_a11y\' field in first test result')
        print_file_content(filename)
        return False

    if 'report_stand' not in first_test_result:
        print('Test failed, missing \'report_stand\' field in first test result')
        print_file_content(filename)
        return False

    if 'date' not in first_test_result:
        print('Test failed, missing \'date\' field in first test result')
        print_file_content(filename)
        return False

    if 'data' not in first_test_result:
        print('Test failed, missing \'data\' field in first test result')
        print_file_content(filename)
        return False

    if int(test_id) != first_test_result['type_of_test']:
        print('Test failed, \'type_of_test\' field is using wrong test id')
        print_file_content(filename)
        return False

    if 'rating' not in first_test_result or\
            'rating_sec' not in first_test_result or\
            'rating_perf' not in first_test_result or\
            'rating_a11y' not in first_test_result or\
            'rating_stand' not in first_test_result:
        print('Test failed, missing one or more rating field(s) in first test result')
        print_file_content(filename)
        return False

    highest_rating = -1.0
    highest_rating = max(first_test_result['rating'], highest_rating)
    highest_rating = max(first_test_result['rating_sec'], highest_rating)
    highest_rating = max(first_test_result['rating_perf'], highest_rating)
    highest_rating = max(first_test_result['rating_a11y'], highest_rating)
    highest_rating = max(first_test_result['rating_stand'], highest_rating)

    if highest_rating == -1.0:
        print('Test failed, no rating was set during the test')
        print_file_content(filename)
        return False

    print('test result exists')
    print_file_content(filename)
    return True

def get_content(url, allow_redirects=False, use_text_instead_of_content=True):
    """Trying to fetch the response content
    Attributes: url, as for the URL to fetch
    """

    try:
        headers = {
            'user-agent': (
                'Mozilla/5.0 (compatible; Windows NT 10.0; Win64; x64) '
                'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.96 '
                'Safari/537.36 Edg/88.0.705.56'
            )
        }

        a = requests.get(url, allow_redirects=allow_redirects,
                         headers=headers, timeout=120)

        if use_text_instead_of_content:
            content = a.text
        else:
            content = a.content
        return content
    except ssl.CertificateError as error:
        print(f'Info: Certificate error. {error.reason}')
    except requests.exceptions.SSLError as error:
        if 'http://' in url:  # trying the same URL over SSL/TLS
            print('Info: Trying SSL before giving up.')
            return get_content(url.replace('http://', 'https://'))
        print(f'Info: SSLError. {error}')
        return ''
    except requests.exceptions.ConnectionError as error:
        if 'http://' in url:  # trying the same URL over SSL/TLS
            print('Connection error! Info: Trying SSL before giving up.')
            return get_content(url.replace('http://', 'https://'))
        print(
            f'Connection error! Unfortunately the request for URL "{url}" failed.'
            f'\nMessage:\n{sys.exc_info()[0]}')
        return ''
    except requests.exceptions.Timeout:
        print(
            f'Timeout error! Unfortunately the request for URL "{url}" timed out. '
            f'The timeout is set to {120} seconds.\n'
            f'Message:\n{sys.exc_info()[0]}')
    except requests.exceptions.RequestException as error:
        print(
            f'Error! Unfortunately the request for URL "{url}" failed for other reason(s).\n'
            f'Message:\n{error}')
    return ''

def set_file(file_path, content, use_text_instead_of_content):
    """
    Writes the provided content to a file at the specified path.

    If 'use_text_instead_of_content' is True,
        the function opens the file in text mode and writes the content as a string.
    If 'use_text_instead_of_content' is False,
        the function opens the file in binary mode and writes the content as bytes.

    Args:
        file_path (str): The path to the file where the content will be written.
        content (str or bytes): The content to be written to the file.
        use_text_instead_of_content (bool): 
            Determines whether the file is opened in text or binary mode.

    Returns:
        None
    """
    if use_text_instead_of_content:
        with open(file_path, 'w', encoding='utf-8', newline='') as file:
            file.write(content)
    else:
        with open(file_path, 'wb') as file:
            file.write(content)

def main(argv):
    """
    WebPerf Core - Regression Test

    Usage:
    verify_result.py -h

    Options and arguments:
    -h/--help\t\t\t: Verify Help command
    -d/--docker <activate feature, True or False>\t\t:
      Updates DockerFile to use latest browsers
    -t/--test <test number>\t: Verify result of specific test

    NOTE:
    If you get this in step "Setup config [...]" you forgot to
    add repository secret for your repository.
    More info can be found here: https://github.com/Webperf-se/webperf_core/issues/81
    """

    try:
        opts, _ = getopt.getopt(argv, "hlt:d:s:b:", [
                                   "help", "test=", "sample-config=",
                                   "browsertime=",
                                   "language", "docker="])
    except getopt.GetoptError:
        print(main.__doc__)
        sys.exit(2)

    if len(opts) == 0:
        print(main.__doc__)
        sys.exit(2)

    for opt, arg in opts:
        if opt in ('-h', '--help'):  # help
            print(main.__doc__)
            sys.exit(0)
        elif opt in ("-s", "--sample-config"):
            handle_sample_config(arg)
        elif opt in ("-t", "--test"):  # test id
            handle_test_result(arg)
        elif opt in ("-d", "--docker"):  # docker
            handle_update_docker()
        elif opt in ("-b", "--browsertime"):  # validate browsertime.har for supported browsers
            handle_validate_browsertime(arg)

    # No match for command so return error code to fail verification
    sys.exit(2)

def get_sitespeed_version_from_package(package_json_filepath):
    """
    Retrieves the version of 'sitespeed.io' from a package.json file.

    This function opens and reads a package.json file. It then checks if 'dependencies' 
    and 'sitespeed.io' are present in the package information. If they are, it returns 
    the version of 'sitespeed.io'. If either 'dependencies' or 'sitespeed.io' is not 
    present, it returns None.

    Args:
        package_json_filepath (str): The path to the package.json file.

    Returns:
        str: The version of 'sitespeed.io' if found, else None.
    """
    with open(package_json_filepath, encoding='utf-8') as json_input_file:
        package_info = json.load(json_input_file)
        if 'dependencies' not in package_info:
            return None
        if 'sitespeed.io' not in package_info['dependencies']:
            return None
        return package_info['dependencies']['sitespeed.io']

def get_base_os_from_dockerfile(docker_content):
    """
    Extracts the base operating system from a Dockerfile content.

    This function uses a regular expression to find the first
    'FROM' instruction in the Dockerfile content. 
    It specifically looks for 'FROM' instructions that
    use 'sitespeedio/webbrowsers' as the base image. 
    If such an instruction is found, it is returned as a string. If not, None is returned.

    Args:
        docker_content (str): The content of the Dockerfile.

    Returns:
        str: The 'FROM' instruction string if found, else None.
    """
    docker_from = None
    regex = r'^(?P<from>FROM sitespeedio\/sitespeed\.io:[^\n\r]+)'
    matches = re.finditer(
        regex, docker_content, re.MULTILINE)
    for _, match_range in enumerate(matches, start=1):
        docker_from = match_range.group('from')
        break
    return docker_from

def set_file_content(file_path, content):
    """
    Writes the given content to a file at the specified path.

    This function checks if the file exists at the given path.
    If the file does not exist, it prints an error message and returns.
    If the file does exist, it opens the file in write mode with UTF-8 encoding and
    writes the provided content to the file.

    Args:
        file_path (str): The path to the file.
        content (str): The content to be written to the file.

    Returns:
        None
    """
    if not os.path.isfile(file_path):
        print(f"ERROR: No {file_path} file found!")
        return

    with open(file_path, 'w', encoding='utf-8', newline='') as file:
        file.write(content)


def handle_update_docker():
    """ Terminate the programme with an error if updating docker contains unexpected content  """
    base_directory = Path(os.path.dirname(
            os.path.realpath(__file__)) + os.path.sep).parent.parent

    package_json_filepath = os.path.join(base_directory, 'package.json')
    if not os.path.exists(package_json_filepath):
        print(f'package.json doesn\'t exists at: {package_json_filepath}')
        return False

    version = get_sitespeed_version_from_package(package_json_filepath)
    print('sitespeed.io version in package.json:', version)

    our_docker_filepath = os.path.join(base_directory, 'Dockerfile')
    if not os.path.exists(our_docker_filepath):
        print(f'Dockerfile doesn\'t exists at: {our_docker_filepath}')
        return False

    our_docker_content = get_file_content(our_docker_filepath)

    our_from_os = get_base_os_from_dockerfile(our_docker_content)
    sitespeed_from_os = f'FROM sitespeedio/sitespeed.io:{version}'

    print('Our Dockerfile:', our_from_os)
    print(f'Sitespeed.io Dockerfile v{version}:', sitespeed_from_os)

    if our_from_os != sitespeed_from_os:
        our_docker_content = our_docker_content.replace(our_from_os, sitespeed_from_os)
        print('Dockerfile requires update')
        set_file_content(our_docker_filepath, our_docker_content)
        print('Dockerfile was updated')

        our_browsertime_har_yml_filepath = os.path.join(base_directory, '.github', 'workflows', 'regression-test-sitespeed-browsertime-har.yml')
        if os.path.exists(our_browsertime_har_yml_filepath):
            our_from_os = our_from_os.replace('FROM ', '')
            sitespeed_from_os = sitespeed_from_os.replace('FROM ', '')

            our_browsertime_har_yml_content = get_file_content(our_browsertime_har_yml_filepath)
            our_browsertime_har_yml_content = our_browsertime_har_yml_content.replace(our_from_os, sitespeed_from_os)
            print('regression-test-sitespeed-browsertime-har.yml requires update')
            set_file_content(our_browsertime_har_yml_filepath, our_browsertime_har_yml_content)
            print('regression-test-sitespeed-browsertime-har.yml was updated')
    else:
        print('Dockerfile is up to date')

    sys.exit(0)

def handle_test_result(arg):
    """ Terminate the programme with an error if our test contains unexpected content  """
    if not validate_failures():
        sys.exit(2)

    if validate_testresult(arg):
        sys.exit(0)
    else:
        sys.exit(2)

def handle_validate_browsertime(browsertime_har_path):
    with open(browsertime_har_path, encoding='utf-8') as json_input_file:
        browsertime_har = json.load(json_input_file)
        if 'log' not in browsertime_har:
            print('Error: log object is missing in browsertime.har file')
            sys.exit(2)

        if 'version' not in browsertime_har['log']:
            print('Error: log.version object is missing in browsertime.har file')
            sys.exit(2)

        if 'creator' not in browsertime_har['log']:
            print('Error: log.creator object is missing in browsertime.har file')
            sys.exit(2)
        if 'name' not in browsertime_har['log']['creator']:
            print('Error: log.creator.name object is missing in browsertime.har file')
            sys.exit(2)
        if 'version' not in browsertime_har['log']['creator']:
            print('Error: log.creator.version object is missing in browsertime.har file')
            sys.exit(2)

        if 'browser' not in browsertime_har['log']:
            print('Error: log.browser object is missing in browsertime.har file')
            sys.exit(2)
        if 'name' not in browsertime_har['log']['browser']:
            print('Error: log.browser.name object is missing in browsertime.har file')
            sys.exit(2)
        if browsertime_har['log']['browser']['name'] not in ('firefox', 'Chrome'):
            print('Error: log.browser.name property has wrong value in browsertime.har file')
            sys.exit(2)

        if 'version' not in browsertime_har['log']['browser']:
            print('Error: log.browser.version object is missing in browsertime.har file')
            sys.exit(2)
        if re.match(r'[0-9\.]+', browsertime_har['log']['browser']['version'], re.IGNORECASE) is None:
            print('Error: log.browser.name property has wrong value in browsertime.har file')
            sys.exit(2)

        if 'pages' not in browsertime_har['log']:
            print('Error: log.pages array is missing in browsertime.har file')
            sys.exit(2)
        page_index = 0
        for page in browsertime_har['log']['pages']:
            if 'id' not in page:
                print(f'log.pages[{page_index}].id object is missing in browsertime.har file')
                sys.exit(2)
            if f'page_{page_index +1 }' not in page['id']:
                print(f'log.pages[{page_index}].id property has wrong value in browsertime.har file')
                sys.exit(2)

            if 'startedDateTime' not in page:
                print(f'log.pages[{page_index}].startedDateTime object is missing in browsertime.har file')
                sys.exit(2)
            if re.match(r'[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}.[0-9]{3}Z', page['startedDateTime']) is None:
                print(f'log.pages[{page_index}].startedDateTime property is wrong value in browsertime.har file')
                sys.exit(2)

            if 'title' not in page:
                print(f'log.pages[{page_index}].title object is missing in browsertime.har file')
                sys.exit(2)
            if 'pageTimings' not in page:
                print(f'log.pages[{page_index}].pageTimings object is missing in browsertime.har file')
                sys.exit(2)

            if '_url' not in page:
                print(f'log.pages[{page_index}]._url object is missing in browsertime.har file')
                sys.exit(2)
            if page['_url'] != 'https://webperf.se':
                print(f'log.pages[{page_index}]._url property has wrong value in browsertime.har file')
                sys.exit(2)

            if '_meta' not in page:
                print(f'log.pages[{page_index}]._meta object is missing in browsertime.har file')
                sys.exit(2)
            page_index += 1
        if page_index < 1:
            print('Error: log.pages array has less than 1 page in browsertime.har file')
            sys.exit(2)

        if 'entries' not in browsertime_har['log']:
            print('Error: log.entries array is missing in browsertime.har file')
            sys.exit(2)
        entity_index = 0
        for entity in browsertime_har['log']['entries']:
            if 'cache' not in entity:
                print(f'log.entries[{entity_index}].id object is missing in browsertime.har file')
                sys.exit(2)
            if 'startedDateTime' not in entity:
                print(f'log.entries[{entity_index}].startedDateTime object is missing in browsertime.har file')
                sys.exit(2)
            if re.match(r'[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}.[0-9]{3}Z', entity['startedDateTime']) is None:
                print(f'log.entries[{entity_index}].startedDateTime property is wrong value in browsertime.har file')
                sys.exit(2)
            if 'timings' not in entity:
                print(f'log.entries[{entity_index}].timings object is missing in browsertime.har file')
                sys.exit(2)
            if 'pageref' not in entity:
                print(f'log.entries[{entity_index}].pageref object is missing in browsertime.har file')
                sys.exit(2)
            if entity['pageref'] != 'page_1':
                print(f'log.entries[{entity_index}].pageref property has wrong value in browsertime.har file')
                sys.exit(2)

            if 'time' not in entity:
                print(f'log.entries[{entity_index}].time object is missing in browsertime.har file')
                sys.exit(2)
            if not isinstance(entity['time'], float):
                print(f'log.entries[{entity_index}].time property has wrong value in browsertime.har file')
                sys.exit(2)

            if 'request' not in entity:
                print(f'log.entries[{entity_index}].request object is missing in browsertime.har file')
                sys.exit(2)

            if 'method' not in entity['request']:
                print(f'log.entries[{entity_index}].request.method object is missing in browsertime.har file')
                sys.exit(2)
            if entity['request']['method'] not in ('GET','POST'):
                print(f'log.entries[{entity_index}].request.method property has wrong value in browsertime.har file')
                sys.exit(2)

            if 'url' not in entity['request']:
                print(f'log.entries[{entity_index}].request.url object is missing in browsertime.har file')
                sys.exit(2)
            if entity_index == 0 and entity['request']['url'] != 'https://webperf.se/':
                print(f'log.entries[{entity_index}].request.url property has wrong value in browsertime.har file')
                sys.exit(2)

            if 'queryString' not in entity['request']:
                print(f'log.entries[{entity_index}].request.queryString object is missing in browsertime.har file')
                sys.exit(2)
            if entity_index == 0 and entity['request']['queryString'] != []:
                print(f'log.entries[{entity_index}].request.queryString property has wrong value in browsertime.har file')
                sys.exit(2)

            if 'headersSize' not in entity['request']:
                print(f'log.entries[{entity_index}].request.headersSize object is missing in browsertime.har file')
                sys.exit(2)
            if 'bodySize' not in entity['request']:
                print(f'log.entries[{entity_index}].request.bodySize object is missing in browsertime.har file')
                sys.exit(2)
            if 'cookies' not in entity['request']:
                print(f'log.entries[{entity_index}].request.cookies array is missing in browsertime.har file')
                sys.exit(2)
            if 'httpVersion' not in entity['request']:
                print(f'log.entries[{entity_index}].request.httpVersion object is missing in browsertime.har file')
                sys.exit(2)
            if 'headers' not in entity['request']:
                print(f'log.entries[{entity_index}].request.headers array is missing in browsertime.har file')
                sys.exit(2)

            if 'response' not in entity:
                print(f'log.entries[{entity_index}].response object is missing in browsertime.har file')
                sys.exit(2)
            if 'redirectURL' not in entity['response']:
                print(f'log.entries[{entity_index}].response.redirectURL object is missing in browsertime.har file')
                sys.exit(2)
            if 'status' not in entity['response']:
                print(f'log.entries[{entity_index}].response.status object is missing in browsertime.har file')
                sys.exit(2)
            if 'statusText' not in entity['response']:
                print(f'log.entries[{entity_index}].response.statusText object is missing in browsertime.har file')
                sys.exit(2)
            if 'content' not in entity['response']:
                print(f'log.entries[{entity_index}].response.content object is missing in browsertime.har file')
                sys.exit(2)
            if 'headersSize' not in entity['response']:
                print(f'log.entries[{entity_index}].response.headersSize object is missing in browsertime.har file')
                sys.exit(2)
            if 'bodySize' not in entity['response']:
                print(f'log.entries[{entity_index}].response.bodySize object is missing in browsertime.har file')
                sys.exit(2)
            if 'cookies' not in entity['response']:
                print(f'log.entries[{entity_index}].response.cookies array is missing in browsertime.har file')
                sys.exit(2)
            if 'httpVersion' not in entity['response']:
                print(f'log.entries[{entity_index}].response.httpVersion object is missing in browsertime.har file')
                sys.exit(2)
            if 'headers' not in entity['response']:
                print(f'log.entries[{entity_index}].response.headers array is missing in browsertime.har file')
                sys.exit(2)

            entity_index += 1
        if entity_index < 1:
            print('Error: log.entries array has less than 1 entry in browsertime.har file')
            sys.exit(2)

    print('browsertime.har file is OK')
    sys.exit(0)

def handle_sample_config(arg):
    """ Terminate the programme with an error if we're unable to
      generate a config.py file from SAMPLE-config with a few alterations """
    if 'true' == arg.lower() or 'false' == arg.lower() or '1' == arg or '0' == arg:
        raise ValueError(
                    'c/prep-config argument has changed format,'
                    ' it doesn\'t support previous format')
    arguments = arg.split(',')

    base_directory = Path(os.path.dirname(
        os.path.realpath(__file__)) + os.path.sep).parent.parent
    if prepare_config_file(
            f'{base_directory}{os.path.sep}defaults{os.path.sep}config.py',
            f'{base_directory}{os.path.sep}defaults{os.path.sep}config.py',
            arguments):
        sys.exit(0)
    else:
        sys.exit(2)

def handle_pre_config(arg):
    """ Terminate the programme with an error if we're unable to
      generate a config.py file from SAMPLE-config with a few alterations """
    if 'true' == arg.lower() or 'false' == arg.lower() or '1' == arg or '0' == arg:
        raise ValueError(
                    'c/prep-config argument has changed format,'
                    ' it doesn\'t support previous format')
    arguments = arg.split(',')

    base_directory = Path(os.path.dirname(
        os.path.realpath(__file__)) + os.path.sep).parent.parent
    if prepare_config_file(
            f'{base_directory}{os.path.sep}defaults{os.path.sep}config.py',
            'config.py',
            arguments):
        sys.exit(0)
    else:
        sys.exit(2)


if __name__ == '__main__':
    main(sys.argv[1:])
