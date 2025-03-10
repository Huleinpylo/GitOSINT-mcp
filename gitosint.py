import argparse
from modules.gitlab import gitlab_find
from modules.bitbucket import bitbucket_find
from modules.gitea import gitea_find
from modules.github import github_find

def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('-u', '--user', type=str, help='Username', required=True)
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose mode')
    return parser.parse_args()

def main():

    print('GitOSINT --- by 0xlildoudou')

    args = parse_arguments()
    verbose = args.verbose

    print('[i] Gitlab')
    result = gitlab_find(args.user, verbose)
    print(result)

    print('[i] Bitbucket')
    result = bitbucket_find(args.user, verbose)
    print(result)

    print('[i] Gitea')
    result = gitea_find(args.user, verbose)
    print(result)

    print('[i] GitHub')
    result = github_find(args.user, verbose)
    print(result)

if __name__ == '__main__':
    main()
