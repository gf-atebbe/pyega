import argparse
import os
import sys
import json
import requests
import uuid

debug = False
version = "1.0.0"

def load_credentials(filepath = "~/.ega.json"):
    """Load credentials for EMBL/EBI EGA from ~/.ega.json"""
    filepath = os.path.expanduser(filepath)
    if not os.path.exists(filepath):
        print("{} does not exist".format(filepath))
        sys.exit(1)
    with open(filepath) as f:
        creds = json.load(f)
    if 'username' not in creds or 'password' not in creds or 'key' not in creds:
        print("{} does not contain either or any of 'username', 'password', or 'key' fields".format(filepath))
        sys.exit(1)

    return (creds['username'], creds['password'], creds['key'])

def api_login(username, password):
    headers = {'Accept': 'application/json'}
    # This looks horrible, but is necessary for both
    # (a) EGA REST API which requires direct JSON (not form encoded) and
    # (b) python requests module, which requries a string (vs dict) to post directly and
    # (c) double {{ / }} escaping necessary when using format()
    data = 'loginrequest={{"username": "{}", "password": "{}"}}'.format(username, password)
    url = "https://ega.ebi.ac.uk/ega/rest/access/v2/users/login"

    r = requests.post(url, headers = headers, data = data)
    if (debug): print( json.dumps(r.text, indent=4) ) 
    reply = r.json()
    
    response = reply['response']
    result = response['result']
    result_type = result[0]
    if result_type == "success":
        print("Login success for user {}".format(username))
        session_token = result[1]
    else:
        print("Login failure for user {}".format(username))
        # TODO: return more useful information about reason for failure?
        session_token = ""

    return session_token

def api_logout(session):
    headers = {'Accept': 'application/json'}
    url = "https://ega.ebi.ac.uk/ega/rest/access/v2/users/logout?session={}".format(session)
    r = requests.get(url, headers = headers)
    print("[Logout]")

def api_list_authorized_datasets(session):
    pass

def list_files_in_dataset(session, dataset):
    pass

def api_list_requests(session, req=""):
    """Requests download tickets (optionally for a given request/label)"""

    if not session:
        print("list_tickets() called with empty session")
        sys.exit(1)

    headers = {'Accept':'application/json'}
    # URL form with no request label: https://ega.ebi.ac.uk/ega/rest/access/v2/requests?session=<uuid>
    # URL form with  a request label: https://ega.ebi.ac.uk/ega/rest/access/v2/requests/{reqlabel}?session=<uuid>
    if req: req = "/" + req # prepend with / to make url conform to above
    url = "https://ega.ebi.ac.uk/ega/rest/access/v2/requests{}?session={}".format(req, session)

    r = requests.get(url, headers)
    reply = r.json()
    if reply['header']['userMessage'] == "OK":
        print("list_requests({}) completed successfully".format(req))
        if(debug): print( json.dumps(reply, indent=4) )
        return reply
    else:
        print("list_requests({}) failed".format(req))
        if(debug): print( json.dumps(reply, indent=4) )
        sys.exit(1)
    
def pretty_print_requests(req_ticket):
    req_labels = {}     # dict to track no. (outstanding) files belonging to request label
    for res in req_ticket['response']['result']:
        req_label = res['label']

        if res['label'] not in req_labels:
            req_labels[req_label] = 0

        req_labels[req_label] += 1

    print("{:36} {}".format("\nRequest label", "N (outstanding) files"))
    print("{:36} {}".format(   "-"*36,         "---------------------"))

    for (label,n) in req_labels.items():
        print("{:36} {}".format(label, n))

def pretty_print_files(req_ticket):
    nresults = req_ticket['response']['numTotalResults']

    print("{:15} ({:12}) {:36} {}".format("Stable ID", "Bytes", "Download ticket", "Remote filename"))
    print("{:15} {:14} {:36} {}".format(  "-"*15,      "-"*14,  "-"*36,            "---------------"))
    for res in req_ticket['response']['result']:
        remote_fileid   = res['fileID']
        remote_filename = res['fileName']
        remote_filesize = res['fileSize']
        download_ticket = res['ticket']

        print("{:15} ({:12}) {} {}".format(remote_fileid, remote_filesize, download_ticket, remote_filename))
    
def api_delete_request(session, req):
    """Delete a single request label"""

    headers = {'Accept':'application/json'}
    url = "https://ega.ebi.ac.uk/ega/rest/access/v2/requests/delete/{}?session={}".format(req, session)
    r = requests.get(url, headers = headers)

    reply = r.json()
    if reply['header']['userMessage'] == "OK":
        print("Deletion request for {} successful".format(req))
        return reply
    else:
        print("Deletion request for {} failed".format(req))
        print("sys.exit(1)")
        sys.exit(1)

def delete_request_ticket(session, req, ticket):
    pass

def api_make_request(session, id_type, stable_id, req_label, key="ega"):
    """Request dataset or file by stable ID"""

    if not session:
        print("make_request() called with empty session")
        sys.exit(1)

    if id_type not in ['datasets','files']:
        print("make_request() called with invalid id_type")
        sys.exit(1)

    if not stable_id:
        print("make_request() called with empty stable_id")
        sys.exit(1)

    headers = {'Accept':'application/json'}
    form = {'rekey':key, 'downloadType': 'STREAM', 'descriptor': req_label}
    data = 'downloadrequest={{"rekey":{},"downloadType":"STREAM","descriptor":{}}}'.format(key, req_label)
    url = "https://ega.ebi.ac.uk/ega/rest/access/v2/requests/new/{}/{}?session={}".format(id_type, stable_id, session)
    r = requests.post(url, headers = headers, data = data)

    reply = json.loads(r.text)
    if reply['header']['userMessage'] == "OK":
        print("Request for {} submitted successfully with label {}".format(stable_id, req_label))
        if(debug): print( json.dumps(reply, indent=4) )
        return reply
    else:
        print("Request for {} was unsuccessful.".format(stable_id))
        if(debug): print( json.dumps(reply, indent=4) )
        sys.exit(1)

def download_request(req_ticket):
    
    if req_ticket['header']['userMessage'] != "OK":
        print("download_request(): request ticket status Not ok")
        sys.exit(1)

    nresults = req_ticket['response']['numTotalResults']
    print("Number of results: {}".format(nresults))

    for res in req_ticket['response']['result']:
        remote_filename = res['fileName']
        remote_filesize = res['fileSize']
        print("Downloading {} ({} bytes)".format(remote_filename, remote_filesize))
        local_filename = os.path.split(remote_filename)[1]

        dl_ticket = res['ticket']
        api_download_ticket(dl_ticket, local_filename)

def api_download_ticket(ticket, local_filename):
    """Download an individual file, encrypted, with a download ticket UUID"""

    url = "http://ega.ebi.ac.uk/ega/rest/ds/v2/downloads/{}".format(ticket)
    print("Requesting {}".format(url))

    with open(local_filename, 'wb+') as fo:
        headers = {'Accept': 'application/octet-stream'}
        r = requests.get(url, headers=headers)
        fo.write(r.content)

def main():
    print("pyEGA version {}".format(version))
    print("James S. Blachly, MD\n")

    parser = argparse.ArgumentParser(description="Download from EMBL EBI's EGA (European Genome-phenome Archive")
    parser.add_argument("-d", "--debug", action="store_true", help="Extra debugging messages")
    # ArgumentParser.add_subparsers([title][, description][, prog][, parser_class][, action][, option_string][, dest][, help][, metavar])
    subparsers = parser.add_subparsers(dest="subcommand", help = "subcommands")

    parser_reqs  = subparsers.add_parser("requests",  help="List outstanding requests")

    parser_rmreq = subparsers.add_parser("rmreq", help="Delete (remove) request label")
    parser_rmreq.add_argument("label", help="Request label to delete")

    parser_files = subparsers.add_parser("files", help="List files (optionally, for a specific request label)")
    parser_files.add_argument("-l", "--label", default="", help="Optional request label")

    parser_fetch = subparsers.add_parser("fetch", help="Fetch a dataset or file")
    parser_fetch.add_argument("identifier", help="Stable id for dataset (e.g. EGAD00000000001) or file (e.g. EGAF12345678901)")
    args = parser.parse_args()
    if args.debug:
        global debug
        debug = True
        print("[debugging]")

    (username, password, key) = load_credentials()
    session = api_login(username, password)
    if not session:
        sys.exit(1)

    if args.subcommand == "requests":
        list_reply = api_list_requests(session)
        pretty_print_requests(list_reply)

    elif args.subcommand == "rmreq":
        api_delete_request(session, args.label)

    elif args.subcommand == "files":
        list_reply = api_list_requests(session, args.label)
        pretty_print_files(list_reply)

    elif args.subcommand == "fetch":
        if (args.identifier[3] == 'D'):
            id_type = "datasets"
        elif(args.identifier[3] == 'F'):
            id_type = "files"
        else:
            print("Unrecognized identifier -- only datasets (EGAD...) and and files (EGAF...) supported")
            sys.exit(1)

        req_label = str( uuid.uuid4() )
        req_reply = api_make_request(session, id_type, args.identifier, req_label, key)

        list_reply = api_list_requests(session, req_label)

        download_request(list_reply)

    api_logout(session)

if __name__ == "__main__":
    main()

