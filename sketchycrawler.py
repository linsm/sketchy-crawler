import csv
import requests
import json
import argparse
import subprocess
import datetime
import os
import time

class CrawlingTarget:
    def __init__(self, repository_url, owner, repository_name, since, until, trusted_maintainers_list, sketchy_files_list, sketchy_file_types_list, release_tag, package_name, package_manager):
        self.repository_url = repository_url
        self.owner = owner
        self.repository_name = repository_name
        self.since = since
        self.until = until
        self.sketchy_files = [x.strip() for x in sketchy_files_list.split(",")]
        self.sketchy_file_types = [x.strip() for x in sketchy_file_types_list.split(",")]
        self.release_tag = release_tag
        self.package_name = package_name
        self.package_manager = package_manager
        self.trusted_maintainers = [x.strip() for x in trusted_maintainers_list.split(",")]

    def __repr__(self):
        return f"CrawlingTarget(repository_url={self.repository_url}, owner={self.owner}, repository_name={self.repository_name}, since={self.since}, until={self.until}, trusted_maintainers={self.trusted_maintainers}, sketchy_files={self.sketchy_files}, sketchy_file_types={self.sketchy_file_types}, release_tag={self.release_tag}, package_name={self.package_name}, package_manager={self.package_manager})"

class Result:
    def __init__(self, repository_url, commits_from_untrusted_maintainer, build_dependencies, package_dependencies, package_reverse_dependencies, cargo_dependencies, sketchy_files, sketchy_files_in_gitignore, sketchy_file_types, differences_in_tarball):
        self.repository_url = repository_url
        self.commits_from_untrusted_maintainer = commits_from_untrusted_maintainer
        self.build_dependencies = build_dependencies
        self.package_dependencies = package_dependencies
        self.package_reverse_dependencies = package_reverse_dependencies
        self.cargo_dependencies = cargo_dependencies
        self.sketchy_files = sketchy_files
        self.sketchy_files_in_gitignore = sketchy_files_in_gitignore
        self.sketchy_file_types = sketchy_file_types
        self.differences_in_tarball = differences_in_tarball

    def to_dict(self):
        return {
            "repository_url": self.repository_url,
            "commits_from_untrusted_maintainer": self.commits_from_untrusted_maintainer,
            "build_dependencies": self.build_dependencies,
            "package_dependencies": self.package_dependencies,
            "package_reverse_dependencies": self.package_reverse_dependencies,
            "cargo_dependencies": self.cargo_dependencies,
            "sketchy_files": self.sketchy_files,
            "sketchy_files_in_gitignore": self.sketchy_files_in_gitignore,
            "sketchy_file_types": self.sketchy_file_types,
            "differences_in_tarball": self.differences_in_tarball
        }

    def __repr__(self):
        return f"Result(repository_url={self.repository_url}, commits_from_untrusted_maintainer={self.commits_from_untrusted_maintainer}, build_dependencies={self.build_dependencies}, package_dependencies={self.package_dependencies}, package_reverse_dependencies={self.package_reverse_dependencies}, cargo_dependencies={self.cargo_dependencies}, sketchy_files={self.sketchy_files}, sketchy_files_in_gitignore={self.sketchy_files_in_gitignore}, sketchy_file_types={self.sketchy_file_types}, differences_in_tarball={self.differences_in_tarball})"

def find_untrusted_maintainers(json_file,trusted_maintainers):   
    with open(json_file, 'r') as file:
        data = json.load(file)
    untrusted_maintainer=[]
    for item in data:
        author = item["commit"]["author"]["name"]
        committer = item["commit"]["committer"]["name"]
        if item["author"] is not None:
            author_login = item["author"]["login"]
        if item["committer"] is not None:
            committer_login = item["committer"]["login"]
        trusted_detected = False
        for trusted_maintainer in trusted_maintainers:
            if trusted_maintainer == committer_login:
                trusted_detected = True             
        if trusted_detected == False and author != committer:
                untrusted_maintainer.append(f"{committer} <{committer_login}>")
    print(f"Found {len(untrusted_maintainer)} commits from an untrusted maintainers in {json_file}.")
    return untrusted_maintainer  
  
def fetch_repository_commits(crawler_target, result_file, token):   

    parameters = {
        'since': crawler_target.since,
        'until': crawler_target.until,
        'per_page': 100,
    }

    headers = {
        'Authorization': f'Bearer {token}'
    }

    result = []
    repo_url = f"https://api.github.com/repos/{crawler_target.owner}/{crawler_target.repository_name}/commits"       
    while True:
        response = requests.get(repo_url, params=parameters, headers=headers)  
        data = response.json()
        result.extend(data)

        links = response.headers.get('Link', '')
        next_page_url = None
        if 'rel="next"' in links:
            next_page_url = links.split(';')[0].strip('<>')            
            if next_page_url:
                repo_url = next_page_url
            else:          
                break
        else:
            break
    print(f"Fetched {len(result)} commits from {crawler_target.repository_url} between {crawler_target.since} and {crawler_target.until}.")
    if result_file:
        with open(result_file, 'w') as file:
            json.dump(result, file, indent=4)
    return result

def read_token(file):
    with open(file, 'r') as f:
        for line in f:
            key, value = line.strip().split('=')
            if key == 'GITHUB_TOKEN':
                return value
    return None

def pars_crawling_targets(target_file):
    crawling_targets = []
    with open(target_file, 'r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            repository_url = row["repository_url"]
            owner = row["owner"]
            repository_name = row["repository_name"]
            since = row["since"]
            until = row["until"]
            trusted_maintainers_list = row["trusted_maintainers"]
            sketchy_files_list = row["sketchy_files"]
            sketchy_file_types_list = row["sketchy_file_types"]
            release_tag = row["release_tag"]
            package_name = row["package_name"]
            package_manager = row["package_manager"]
            crawling_target = CrawlingTarget(
                repository_url=repository_url,
                owner=owner,
                repository_name=repository_name,
                since=since,
                until=until,
                trusted_maintainers_list=trusted_maintainers_list,
                sketchy_files_list=sketchy_files_list,
                sketchy_file_types_list=sketchy_file_types_list,
                release_tag=release_tag,
                package_name=package_name,
                package_manager=package_manager
            )
            crawling_targets.append(crawling_target)
    print(f"Found {len(crawling_targets)} crawling targets.")
    return crawling_targets


def crawl_target(target):
    
    print(f"Crawling target: {target.repository_url}")

    # Step 1: Fetch commits from repositories 
    commits = []
    commit_file_name = f"results/{target.owner}-{target.repository_name}"
    if os.path.exists(commit_file_name):
        print("Skipping commit fetching as commits file is provided.")
    else:
        commits = fetch_repository_commits(target, f"results/{target.owner}-{target.repository_name}", read_token('.env'))
        
    # Step 2: Find if there are untrusted maintainers pushing to the repository
    print("Finding untrusted maintainers...")
    trusted_maintainers = target.trusted_maintainers
    commits_from_untrusted_maintainer = find_untrusted_maintainers(commit_file_name, trusted_maintainers)

    # Step 3: Analyse dependencies
    print("Analysing dependencies...")
    output = subprocess.run(["./helper-scripts/dependency_counter_apt.sh", f"{target.package_name}"], text=True, capture_output=True)
    result = output.stdout.strip()
    build_dependencies, package_dependencies, reverse_dependencies = result.split()
    if build_dependencies == "100":
        print(f"The package {target.package_name} has >={build_dependencies} build dependencies.")
    else:
        print(f"The package {target.package_name} has {build_dependencies} build dependencies.")
    print(f"The package {target.package_name} has {package_dependencies} package dependencies.")
    print(f"The package {target.package_name} has {reverse_dependencies} reverse dependencies.")
    dependencies_cargo = "N/A"
    if target.package_manager == "cargo":
        print("Fetching dependencies for cargo...")
        output_cargo = subprocess.run(["./helper-scripts/dependency_counter_cargo.sh", f"tmp/{target.package_name}"], text=True, capture_output=True)
        result_cargo = output_cargo.stdout.strip()
        dependencies_cargo = result_cargo.split()
        print(f"The package {target.package_name} has {dependencies_cargo} dependencies in cargo.")

    # Step 4 and 5: Find sketchy files
    print("Finding sketchy files...")
    sketchy_file_list = ",".join(target.sketchy_files)
    sketch_file_type_list = ",".join(target.sketchy_file_types)
    output = subprocess.Popen(["./helper-scripts/find_sketchy_files.sh", target.repository_url, f"{target.repository_name}", f"{sketchy_file_list}", f"{sketch_file_type_list}"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    sketchy_files = 0
    sketchy_file_types = 0

    stdout, stderr = output.communicate()
    lines = stdout.splitlines()
    for i, line in enumerate(lines):
        if i == len(lines)-1:
            sketchy_files, sketchy_file_types = line.strip().split()
        else:
            print(line.strip())

    # find sketchy files in .gitignore
    # check if .gitignore file exists
    gitignore_file = f"tmp/{target.repository_name}/.gitignore"
    if os.path.exists(gitignore_file):
        print(f"Finding sketchy files in {gitignore_file}...")
        output_gitignore = subprocess.run(["./helper-scripts/find_sketchy_files_in_gitignore.sh", f"{gitignore_file}", f"{sketchy_file_list}"], text=True, capture_output=True)
        result_gitignore = output_gitignore.stdout.strip()
        print(f"Sketchy files in .gitignore: {result_gitignore}")   

    # Find differences between source tarball and repository
    print("Finding differences between source tarball and repository...")
    output_diff = subprocess.run(["./helper-scripts/diff_source.sh", f"{target.owner}", f"{target.repository_name}", f"{target.release_tag}"], text=True, capture_output=True)
    result_diff = output_diff.stdout.strip()
    print(f"Found {result_diff} different files between source tarball and repository.")

    final_result = Result(
        repository_url=target.repository_url,
        commits_from_untrusted_maintainer=len(commits_from_untrusted_maintainer),
        build_dependencies=build_dependencies,
        package_dependencies=package_dependencies,
        package_reverse_dependencies=reverse_dependencies,
        cargo_dependencies=dependencies_cargo,
        sketchy_files=sketchy_files,
        sketchy_files_in_gitignore=result_gitignore,
        sketchy_file_types=sketchy_file_types,
        differences_in_tarball=result_diff
    )        
    return final_result

def full_run(args):
    start_time = time.time()
    print("Starting full run to find sketchy things...")
    crawling_targets = pars_crawling_targets(args.targets)
    
    results = []
    for target in crawling_targets:        
        result = crawl_target(target)
        print(result)
        results.append(result)

    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"Elapsed time: {elapsed_time:.2f} seconds")
    print("Saving results to JSON file...")

    current_time = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"results/results_{current_time}.json"

    results_dict = [result.to_dict() for result in results]

    with open(filename, 'w') as file:  
        json.dump(results_dict, file, indent=4)

def fetch_commits(args):
    print("Fetching commits...")
    token = read_token('.env')    
    fetch_repository_commits(args.source_file, args.target_file, token)

def find_maintainer_change(args):
    print("Crawling JSON...")
    crawling_targets = pars_crawling_targets(args.repository_file)
    find_untrusted_maintainers(args.json_file, crawling_targets[0].trusted_maintainers)

def analyse_dependencies(args):
    print("Fetching reverse dependencies...")
    output = subprocess.run(["./helper-scripts/dependency_counter_apt.sh", "liblzma5"], text=True, capture_output=True)
    result = output.stdout.strip()
    dependencies, reverse_dependencies = result.split()
    print(f"Dependencies: {dependencies}")
    print(f"Reverse Dependencies: {reverse_dependencies}")    

def find_sketchy_files(repo_url):
    print("Finding sketchy files...")
    output = subprocess.run(["./helper-scripts/find_sketchy_files.sh", "https://github.com/tukaani-project/xz.git", "xz", "configure.ac"], text=True, capture_output=True)       
    print(output.stdout.strip())    

def cleanup():
    print("Cleaning up...")
    if os.path.exists("tmp"):
        os.rmdir("tmp")

def main():
    parser = argparse.ArgumentParser(description='Backdoor Crawler')
    subparsers = parser.add_subparsers(dest='command', required=True)

    parser_full_run = subparsers.add_parser('fullrun', help='Fetch commits from repositories')
    parser_full_run.add_argument('--targets', type=str, required=True, help='Path to the CSV file containing crawling targets.')
    parser_full_run.set_defaults(func=full_run)

    parser_fetch_commits = subparsers.add_parser('fetchcommits', help='Fetch commits from repositories')
    parser_fetch_commits.add_argument('--source_file', type=str, required=True, help='Path to the source CSV file')
    parser_fetch_commits.add_argument('--target_file', type=str, required=True, help='Path to the target JSON file')
    parser_fetch_commits.set_defaults(func=fetch_commits) 

    parser_find_maintainer_change = subparsers.add_parser('findmaintainerchange', help='Crawl JSON for trusted maintainers')
    parser_find_maintainer_change.add_argument('--repository_file', type=str, required=True, help='Path to the source CSV file')
    parser_find_maintainer_change.add_argument('--json_file', type=str, required=True, help='Path to the source JSON file')
    parser_find_maintainer_change.add_argument('--repository', type=str, required=True, help='Repository name')
    parser_find_maintainer_change.set_defaults(func=find_maintainer_change) 

    parser_dependencies = subparsers.add_parser('fetchreverse', help='Fetch reverse dependencies')
    parser_dependencies.set_defaults(func=analyse_dependencies)

    parser_find_sketchy_files = subparsers.add_parser('findsketchyfiles', help='Find sketchy files')
    parser_find_sketchy_files.add_argument('--repository_url', type=str, required=True, help='Repo URL')
    parser_find_sketchy_files.set_defaults(func=find_sketchy_files)

    args = parser.parse_args()
    args.func(args)

if __name__ == "__main__":    
    main()