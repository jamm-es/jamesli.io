import json
import os
import shutil
import stat
import subprocess
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup

with open('config.json') as c:
    config = json.load(c)


# used to chmod read only files when doing rmtree
def remove_readonly(func, path, _):
    os.chmod(path, stat.S_IWRITE)
    func(path)


# setup output and working dirs

# output dir
if os.path.exists(config['outputPath']):
    shutil.rmtree(config['outputPath'], onerror=remove_readonly)
os.mkdir(config['outputPath'])

# working dir
if os.path.exists(config['workingPath']):
    shutil.rmtree(config['workingPath'], onerror=remove_readonly)
os.mkdir(config['workingPath'])


# generate projects

for project in config['projects']:

    # validate

    # validate required keys
    required_keys = ['serves', 'source']
    for required in required_keys:
        if required not in project:
            raise Exception(f'Required key "{required}" not in project')

    # validate build command keys
    build_keys = ['buildCommands', 'buildOutput']
    has_all_build_keys = True
    has_no_build_keys = True
    for build in build_keys:
        if build in project:
            has_no_build_keys = False
        else:
            has_all_build_keys = False
    if has_all_build_keys == has_no_build_keys:
        raise Exception(f'Has one but not all build keys')


    # copy git repo or path to working directory

    # clear out working directory
    shutil.rmtree(config['workingPath'], onerror=remove_readonly)

    # case where it's a url
    url = urlparse(project['source'])
    if bool(url.scheme):
        subprocess.run(f'git clone --depth=1 {project["source"]} {config["workingPath"]}', shell=True)

    # case where it's a path - copy contents to working directory
    elif os.path.exists(project['source']):
        shutil.copytree(project['source'], config['workingPath'])

    # raise exception where it's neither a valid path nor a valid url
    else:
        raise Exception(f'"{project["source"]}" is neither a valid path nor valid url')

    # fix serves url to not have initial slash
    relative_url = project['serves']
    if relative_url[0] == '/':
        relative_url = relative_url[1:]

    # building project

    # if there are build commands, run them
    if has_all_build_keys:
        # if it exists, set "homepage" property in package.json
        package_path = os.path.join(config['workingPath'], 'package.json')
        if os.path.exists(package_path):
            with open(package_path, 'r') as f:
                package = json.load(f)
            package['homepage'] = os.path.join('/', relative_url)
            with open(package_path, 'w') as f:
                json.dump(package, f)
        for command in project['buildCommands']:
            subprocess.run(command, cwd=config['workingPath'], shell=True)
        copy_from = os.path.join(config['workingPath'], project['buildOutput'])
    else:
        # when there isn't a build command, fix all relative file paths
        path_to_begin = '/' + relative_url if len(relative_url) != 0 and relative_url[-1] == '/' else '/' + relative_url + '/'
        for dirpath, dirnames, filenames in os.walk(config['workingPath']):
            for filename in filenames:
                path = os.path.join(dirpath, filename)
                if(path[-5:] != '.html'):
                    continue
                with open(path, 'r') as f:
                    soup = BeautifulSoup(f, 'html.parser')
                for script_tag in soup.find_all('script', src=True):
                    if urlparse(script_tag['src']).netloc == '':
                        script_tag['src'] = urljoin(path_to_begin, script_tag['src'])
                for link_tag in soup.find_all('link', rel='stylesheet', href=True):
                    if urlparse(link_tag['href']).netloc == '':
                        link_tag['href'] = urljoin(path_to_begin, link_tag['href'])
                with open(path, 'w') as f:
                    f.write(str(soup))
        copy_from = config['workingPath']

    # copy completed files into public directory - different function is needed to not copy dir if relative url is root
    copy_to = os.path.join(config['outputPath'], relative_url)
    if relative_url == '':
        for home_path in os.listdir(copy_from):
            home_copy_from = os.path.join(copy_from, home_path)
            home_copy_to = os.path.join(copy_to, home_path)
            if os.path.isfile(home_copy_from):
                shutil.copyfile(home_copy_from,home_copy_to)
            else:
                shutil.copytree(home_copy_from, home_copy_to)
    else:
        shutil.copytree(copy_from, copy_to)
