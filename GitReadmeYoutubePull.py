#!/usr/bin/python3

import csv
import github3
import time
import re
import argparse
from secrets import username, password
import urllib.request
import json

# API rate limit for authenticated requests is way higher than anonymous, so login.
gh = github3.login(username, password=password)
# gh = github3.GitHub() # Anonymous


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("filepath", type=str, metavar="filepath", help="Filepath to the input csv file.")

    args = parser.parse_args()

    return args


def get_row_count(filename):
    with open(filename, 'r') as file:
        return sum(1 for _ in csv.reader(file))


def get_repositories(link):
    if gh.rate_limit()['resources']['search']['remaining'] == 0:
        print("API rate exceeded, sleeping for {0} seconds.".format(gh.rate_limit()['resources']['search']['reset'] - int(time.time()+1)))
        time.sleep(gh.rate_limit()['resources']['search']['reset'] - int(time.time()+1))

    return gh.search_repositories(link.replace("https://github.com/", "", 1), "", 1)


def repo_search(full_name):
    for repo in gh.search_repositories(full_name, "", 1):
        return repo

    return None


def get_redirection(full_name):
    try:
        json_object = json.loads(urllib.request.urlopen('https://api.github.com/repos/{0}'.format(full_name)).read().decode('utf-8'))
    except urllib.error.HTTPError:
        return None

    return json_object["full_name"]


def get_repository(link):
    if gh.rate_limit()['resources']['search']['remaining'] == 0:
        print("API rate exceeded, sleeping for {0} seconds.".format(gh.rate_limit()['resources']['search']['reset'] - int(time.time()+1)))
        time.sleep(gh.rate_limit()['resources']['search']['reset'] - int(time.time()+1))

    full_name = link.replace("https://github.com/", "", 1)

    r = repo_search(full_name)
    if r:
        return r

    redirection_name = get_redirection(full_name)
    if redirection_name is None:
        return None

    return get_repository(redirection_name)


def main():
    filepath = parse_args().filepath
    if not filepath.endswith('.csv'):
        print("Input file must be a .csv file.")
        exit()

    p = re.compile(r"http(?:s?):\/\/(?:www\.)?youtu(?:be\.com\/watch\?v=|\.be\/)([\w\-\_]*)(&(amp;)?‌​[\w\?‌​=]*)?") # From http://stackoverflow.com/a/3726073/6549676
    row_count = get_row_count(filepath)

    with open(filepath, 'r') as infile, open(filepath[:3] + "_ytlinks.csv", "w") as outfile:
        reader = csv.reader(infile)
        next(reader, None)  # Skip header

        writer = csv.writer(outfile)
        writer.writerow(["Youtube Link", "Name", "GitHub Link"])  # Write header

        for i, (timestamp, name, studentid, gitlink) in list(enumerate(reader)):
            # repo = None
            try:
                repo = get_repository(gitlink)
            except LookupError:
                print('GitHub repo {0} not found.'.format(gitlink))
                continue

            if repo is None:
                writer.writerow(['Invalid GitLink.', name, gitlink])
                continue

            readme = repo.repository.readme().decoded
            if not readme:
                writer.writerow(['No ReadMe Found.', name, gitlink])
                continue

            if type(readme) is bytes:
                readme = readme.decode('utf-8')

            ids = p.findall(readme)
            # print(p.search(readme).group(0)) # I think one or two repos had multiple YT vids.
            if len(ids) != 0:
                ids = ids[0]

            ids = [x for x in ids if x]

            for _id in ids:
                writer.writerow(['https://www.youtube.com/watch?v={0}'.format(_id), name, gitlink])

            if not ids:
                writer.writerow(['No Youtube Link Found', name, gitlink])

            print('Processed row {0} out of {1}'.format(i, row_count))

    print("Finished.")

if __name__ == "__main__":
    main()
