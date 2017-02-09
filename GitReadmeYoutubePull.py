#!/usr/bin/python3

import csv
import github3
import time
import re
import argparse
from secrets import username, password

# API rate limit for authenticated requests is way higher than anonymous, so login.
gh = github3.login(username, password=password)
# gh = github3.GitHub() # Anonymous


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("filepath", type=str, metavar="filepath", help="Filepath to the input csv file.")

    args = parser.parse_args()
    args = vars(args)  # Turn into dict-like view.

    return args


def get_row_count(filename):
    with open(filename, 'r') as file:
        return sum(1 for row in csv.reader(file))


def get_repositories(link):
    if gh.rate_limit()['resources']['search']['remaining'] == 0:
        print("API rate exceeded, sleeping for {0} seconds.".format(gh.rate_limit()['resources']['search']['reset'] - int(time.time()+1)))
        time.sleep(gh.rate_limit()['resources']['search']['reset'] - int(time.time()+1))

    return gh.search_repositories(link.replace("https://github.com/", "", 1), "", 1)


def main():
    filepath = parse_args()['filepath']
    if not filepath.endswith('.csv'):
        print("Input file must be a .csv file.")
        exit()

    p = re.compile(r"http(?:s?):\/\/(?:www\.)?youtu(?:be\.com\/watch\?v=|\.be\/)([\w\-\_]*)(&(amp;)?‌​[\w\?‌​=]*)?") # From http://stackoverflow.com/a/3726073/6549676
    row_counter = 0
    row_count = get_row_count(filepath)

    with open(filepath, 'r') as infile, open(filepath[:3] + "_ytlinks.csv", "w") as outfile:
        reader = csv.reader(infile)
        next(reader, None)  # Skip header

        writer = csv.writer(outfile)
        writer.writerow(["Youtube Link", "Name", "GitHub Link"])  # Write header

        for row in reader:
            for repo in get_repositories(row[3]):
                readme = repo.repository.readme().decoded
                if not readme:
                    readme = "No Youtube link found."

                if type(readme) is bytes:
                    readme = readme.decode('utf-8')

                ids = p.findall(readme)
                if len(ids) != 0:
                    ids = ids[0]

                ids = [x for x in ids if x]

                for _id in ids:
                    writer.writerow(['https://www.youtube.com/watch?v={0}'.format(_id), row[1], row[3]])

                if len(ids) == 0:
                    writer.writerow(['No Youtube Link Found', row[1], row[3]])

            print('Processed row {0} out of {1}'.format(row_counter, row_count))
            row_counter += 1

    print("Finished.")

if __name__ == "__main__":
    main()