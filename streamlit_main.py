'''
This streamlit app shows information about GitHub forks.
'''

import streamlit as st
import requests
import json
import os

import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go




if os.path.exists('./.streamlit/secrets.toml'):
    # read GITHUB_AUTH_TOKEN from secrets.toml
    GITHUB_AUTH_TOKEN = st.secrets['github_auth_token']
else:
    # read GITHUB_AUTH_TOKEN from environment variable
    if 'GITHUB_AUTH_TOKEN' in os.environ:
        GITHUB_AUTH_TOKEN = os.environ['GITHUB_AUTH_TOKEN']
    else:
        GITHUB_AUTH_TOKEN = None


if GITHUB_AUTH_TOKEN:
    headers = {'Authorization': 'token {}'.format(GITHUB_AUTH_TOKEN)}
else:
    headers = {}



# def get_forks(repo):
        # '''
        # Get forks of a repository.
        # '''
        # url = 'https://api.github.com/repos/{}/forks'.format(repo)
        # if GITHUB_AUTH_TOKEN:
            # headers = {'Authorization': 'token {}'.format(GITHUB_AUTH_TOKEN)}
        # else:
            # headers = {}
        # response = requests.get(url, headers=headers)
        # response.raise_for_status()
        # return response.json()

# all pages
@st.cache(ttl=3600, suppress_st_warning=True)
def get_forks(repo):
    url = 'https://api.github.com/repos/{}/forks'.format(repo)
    forks = []
    while url:
        response = requests.get(url, headers=headers)
        data = json.loads(response.text)
        check_rate_limit_exceeded(data)
        response.raise_for_status()
        forks.extend(response.json())
        if 'next' in response.links:
            url = response.links['next']['url']
        else:
            url = None

    return forks


# print all forks streamlit
def print_forks(forks):
    st.write('Forks:')
    st.write(forks)


def get_url_fork(repo):
    url = 'https://api.github.com/repos/{}/forks'.format(repo)
    response = requests.get(url, headers=headers)
    data = json.loads(response.text)
    check_rate_limit_exceeded(data)
    response.raise_for_status()
    return response.json()

def print_fork_urls(forks):
    st.write('Forks:')
    for fork in forks:
        st.write(fork['html_url'])

@st.cache(ttl=3600, suppress_st_warning=True)
def get_commits(repo):
    '''
    Get all commits for a repo.
    '''
    url = 'https://api.github.com/repos/{}/commits'.format(repo)
    print("url:", url)
    commits = []
    while url:
        response = requests.get(url)
        data = json.loads(response.text)
        check_rate_limit_exceeded(data)

        # commits.extend(json.loads(response.text))
        commits.extend(response.json())
        if 'next' in response.links:
            url = response.links['next']['url']
        else:
            url = None
    return commits

@st.cache(ttl=3600, suppress_st_warning=True)
def get_commits_forks(forks):
    repos = {}
    for fork in forks:
        url = 'https://api.github.com/repos/{}/commits'.format(fork['full_name'])
        commits = []
        while url:
            response = requests.get(url, headers=headers)
            data = json.loads(response.text)
            check_rate_limit_exceeded(data)
            response.raise_for_status()
            commits.extend(response.json())
            if 'next' in response.links:
                url = response.links['next']['url']
            else:
                url = None

        repos[fork['full_name']] = commits

    return repos

def get_commit_hashes(repo):
    commits = get_commits(repo)
    commit_hashes = []
    for commit in commits:
        commit_hashes.append(commit['sha'])
    return commit_hashes


def get_diff_commits_base_forks(repo):
    forks = get_forks(repo)
    commits = get_commits_forks(forks)
    commits_base = get_commits(repo)
    base_commit_hashes = get_commit_hashes(repo)
    repo_diff_commits = {}
    for fork in forks:
        repo_diff_commits[fork['full_name']] = []
        for commit in commits[fork['full_name']]:
            if commit['sha'] not in base_commit_hashes:
                repo_diff_commits[fork['full_name']].append(commit)

    return repo_diff_commits


def get_num_diff_commits_per_fork(repo_diff_commits):
    num_diff_commits_per_fork = {}
    for fork in repo_diff_commits:
        num_diff_commits_per_fork[fork] = len(repo_diff_commits[fork])
    return num_diff_commits_per_fork


def get_forks_with_commits(repo_diff_commits):
    forks_with_commits = []
    for fork in repo_diff_commits:
        if repo_diff_commits[fork]:
            forks_with_commits.append(fork)
    return forks_with_commits

def print_forks_with_commits_sorted(forks_with_commits, num_diff_commits_per_fork):
    for fork in sorted(forks_with_commits, key=lambda fork: num_diff_commits_per_fork[fork], reverse=True):
        # st.write(fork, ':', num_diff_commits_per_fork[fork])
        # as link
        url_fork = 'https://github.com/' + fork
        print("url_fork:", url_fork)
        st.markdown(f'[{fork}]({url_fork}) : {num_diff_commits_per_fork[fork]}')

def print_commit_messages_per_fork(repo_diff_commits):
    # heading
    st.header('Commit messages per fork')
    # for fork in repo_diff_commits:
        # if repo_diff_commits[fork]:
            # st.write(fork)
            # for commit in repo_diff_commits[fork]:
                # st.write(commit['commit']['message'])

    # sorted
    for fork in sorted(repo_diff_commits, key=lambda fork: len(repo_diff_commits[fork]), reverse=True):
        if repo_diff_commits[fork]:
            # st.write(fork)
            # bold
            # st.markdown(f'**{fork}**')
            # links
            url_fork = 'https://github.com/' + fork
            print("url_fork:", url_fork)
            st.markdown(f'[{fork}]({url_fork})')
            for commit in repo_diff_commits[fork]:
                # st.write(commit['commit']['message'])
                # in code style
                st.code(commit['commit']['message'])


def get_forks_filtered_sorted(repo_diff_commits, num_diff_commits_per_fork):
    forks_filtered_sorted = []
    for fork in sorted(repo_diff_commits, key=lambda fork: num_diff_commits_per_fork[fork], reverse=True):
        if repo_diff_commits[fork]:
            forks_filtered_sorted.append(fork)
    return forks_filtered_sorted

def plot_num_commits_per_fork_sorted(num_diff_commits_per_fork, forks_filtered_sorted):
    print("num_diff_commits_per_fork:", num_diff_commits_per_fork)
    num_commits_list = []
    for fork in forks_filtered_sorted:
        num_commits_list.append(num_diff_commits_per_fork[fork])
    # plot using plotly and add labels
    fig = px.bar(x=forks_filtered_sorted, y=num_commits_list, labels={'x': 'Forks', 'y': 'Number of commits'})
    st.plotly_chart(fig)


def get_dates_last_commit(repo_diff_commits):
    dates_last_commit = {}
    for fork in repo_diff_commits:
        if repo_diff_commits[fork]:
            dates_last_commit[fork] = repo_diff_commits[fork][0]['commit']['author']['date']
    return dates_last_commit

def plot_dates_last_commits_per_fork(dates_last_commit, forks_filtered_sorted):
    st.header('Dates of last commit per fork')
    dates_last_commit_list = []
    for fork in forks_filtered_sorted:
        dates_last_commit_list.append(dates_last_commit[fork])
    # plot on a timeline
    # fig = px.line(x=forks_filtered_sorted, y=dates_last_commit_list)
    # points
    fig = px.scatter(x=forks_filtered_sorted, y=dates_last_commit_list)
    st.plotly_chart(fig)

def check_rate_limit_exceeded(json_response):
    if 'message' in json_response and 'rate limit exceeded' in json_response['message']:
        print(json_response['message'])
        # print in streamlit as error
        st.error(json_response['message'])
        # stop
        st.stop()

# main
def main():
    input_repo = st.text_input('Enter a repo name or url:')
    input_repo = input_repo.strip().replace('https://github.com/', '')
    if input_repo:
        # add it to the url
        print("input_repo:", input_repo)
        user = input_repo.split('/')[0]
        repo = input_repo.split('/')[1]
        st.experimental_set_query_params(user=user, repo=repo)
        base_repo = input_repo
    else:
        # get it from the url
        params = st.experimental_get_query_params()
        if 'repo' in params and 'user' in params:
            base_repo = '{}/{}'.format(params['user'][0], params['repo'][0])
        else:
            return


    # st.title('GitHub Forks Information')
    st.header('GitHub forks with modifications')
    forks = get_forks(base_repo)
    num_forks = len(forks)
    # st.write('Number of forks:', num_forks)
    # urls
    # print_fork_urls(forks)
    # diff
    repo_diff_commits = get_diff_commits_base_forks(base_repo)
    # print("repo_diff_commits:", repo_diff_commits)
    # print('============')
    num_diff_commits_per_fork = get_num_diff_commits_per_fork(repo_diff_commits)
    # print("num_diff_commits_per_fork:", num_diff_commits_per_fork)
    # st.write('Number of commits per fork:')
    # st.write(num_diff_commits_per_fork)
    forks_with_commits = get_forks_with_commits(repo_diff_commits)
    # st.write('Forks with commits:')
    # st.write(forks_with_commits)
    print_forks_with_commits_sorted(forks_with_commits, num_diff_commits_per_fork)
    forks_filtered_sorted = get_forks_filtered_sorted(repo_diff_commits, num_diff_commits_per_fork)
    print("forks_filtered_sorted:", forks_filtered_sorted)
    plot_num_commits_per_fork_sorted(num_diff_commits_per_fork, forks_filtered_sorted)
    print_commit_messages_per_fork(repo_diff_commits)
    dates_last_commit = get_dates_last_commit(repo_diff_commits)
    print("dates_last_commit:", dates_last_commit)
    plot_dates_last_commits_per_fork(dates_last_commit, forks_filtered_sorted)


    # st.write('Diff commits:')
    # st.write(repo_diff_commits)
    # print_forks(forks)


if __name__ == '__main__':
    main()



