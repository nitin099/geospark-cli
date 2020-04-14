import click
import requests


BASE_URL = ''


def process_requests(request_type,
                     url_path,
                     data={}):
    """
    Processes diffrent http requests.
    """
    url = f'{BASE_URL}{url_path}'
    headers = {'Authorization': get_token()} if get_token() else {}
    try:
        if request_type == "GET":
            response = requests.get(url, headers=headers)
        elif request_type == "POST":
            response = requests.post(url, json=data, headers=headers)
        elif request_type == "PUT":
            response = requests.put(url, json=data, headers=headers)
        elif request_type == "DELETE":
            response = requests.delete(url, headers=headers)

        if response.status_code == 400:
            if response.json()["msg"] == "Token is expired.":
                print_red("Please login.")
                return
            elif response.json()['data'].get('name'):
                print_red("App name: " + response.json()['data']['name'][0])
                return
            elif response.json()['data'].get('non_field_error'):
                print_red(response.json()['data']['non_field_error'][0])
                return
            elif response.json()['data'].get('bundle_id') or response.json()['data'].get('package_name'):
                key = list(response.json()['data'].keys())[0]
                print_red(f'{key}: This field is required.')
                return
            click.echo('Request failed')
        return response.json()

    except Exception:
        return


def store_data(data):
    """
    Stores data in hidden file.
    """
    file = open(".token.txt", "w+")
    file.write(data)
    file.close()
    return None


def get_token():
    """
    Returns the stored data in the file.
    """
    try:
        file = open(".token.txt", "r")
        return file.read()
    except FileNotFoundError:
        return None


def print_purple(inp):
    """
    Prints input in purple colour.
    """
    print("\033[95m{}\033[00m".format(inp))


def print_red(inp):
    """
    Prints input in red colour.
    """
    print("\033[91m{}\033[00m".format(inp))


@click.group()
def geospark_cli():
    """
    Geospark CLI
    """


@geospark_cli.command()
def login():
    """
    Login with Geospark account.
    """
    email = click.prompt("Email", type=str)
    password = click.prompt("Password", hide_input=True)
    data = {
        "email": email,
        "password": password
    }
    resp = process_requests("POST", "/accounts/login/", data)
    token = resp['data'].get('token')
    if token:
        store_data(token)
    print_purple("Login successful .....")
    return None


def create_project():
    name = click.prompt("Enter project name", type=str)
    data = {'name': name}
    resp = process_requests("POST", "/projects/", data=data)
    project = resp.get('data')
    proj_name = project['name']
    print_purple(f'{proj_name} project created successfully')
    return


@geospark_cli.command()
def projects():
    """
    Performs all the project related operations.
    """
    try:
        project_dict = dict()
        resp = process_requests("GET", "/projects/")
        if not resp:
            return

        if not resp['data']:
            click.echo("No projects found.\nCreate a project.")
            create_project()
            return

        for num, project in enumerate(resp['data']):
            proj_name = project['name']
            click.echo(f'{num+1} {proj_name}')
            project_dict[num + 1] = {'Name': proj_name,
                                     'Publishable key': project['publish_key'],
                                     "Secret API key": project['secret_api_key'],
                                     "id": project["id"]
                                     }
        proj_num = click.prompt('Please select a project or enter 0 to create a new project',
                                type=int)
        click.echo('')
        if proj_num == 0:
            name = click.prompt("Enter project name", type=str)
            data = {'name': name}
            resp = process_requests("POST", "/projects/", data=data)
            project = resp.get('data')
            proj_name = project['name']
            print_purple(f'{proj_name} project created successfully')
            return

        for k, v in project_dict[int(proj_num)].items():
            if k == "id":
                continue
            click.echo(f'{k}: {v}')
        click.echo('')
        inp = click.prompt('What to do?  \n 1 Modify \n 2 Delete', type=int)

        if inp == 0:
            create_project()

        elif inp == 1:
            name = click.prompt("Update project name", type=str)
            data = {'name': name}
            proj_id = project_dict[proj_num]['id']
            resp = process_requests("PUT", f"/projects/{proj_id}/", data=data)
            project = resp.get('data')
            proj_name = project['name']
            print_purple(f'{proj_name} project updated successfully')

        elif inp == 2:
            proj_name = project_dict[proj_num]['Name']
            confirm = click.prompt(f"Are you sure (Y or N) project {proj_name}", type=str)
            if confirm.lower() == 'n':
                return
            proj_id = project_dict[proj_num]['id']
            resp = process_requests("DELETE", f"/projects/{proj_id}/")
            print_purple(f'{proj_name} project deleted successfully')
        else:
            return

    except Exception:
        click.echo('Quit')


@geospark_cli.command()
def apps():
    """
    Performs all the apps related operations.
    """
    try:
        project_dict = dict()
        app_dict = dict()
        resp = process_requests("GET", "/projects/")
        for num, project in enumerate(resp['data']):
            proj_name = project['name']
            click.echo(f'{num+1} {proj_name}')
            project_dict[num + 1] = {'apps': project['apps'],
                                     "id": project["id"]
                                     }

        proj_num = click.prompt('Please select a project', type=int)
        click.echo('')
        proj_id = project_dict[proj_num]['id']

        for num, app in enumerate(project_dict[int(proj_num)]['apps']):
            app_name = app['name']
            click.echo(f'{num+1} {app_name}')
            app_dict[num + 1] = {
                'Name': app_name,
                'App platform': "Android" if app['app_platform'] == 1 else 'iOS',
                'app_id': app['app_id']
            }
            if app['package_name']:
                app_dict[num + 1].update({'Package name': app['package_name']})
            else:
                app_dict[num + 1].update({'Bundle Id': app['bundle_id']})

        if not project_dict[int(proj_num)]['apps']:
            click.echo("No apps found")
            app_num = click.prompt('Select 0 to create new app', type=int)
        else:
            app_num = click.prompt('Select an app or 0 to create new app', type=int)
            click.echo('')

        if app_num == 0:
            app_platform = click.prompt("Select the app want to create 1 Android, 2 iOS", type=int)
            app_name = click.prompt("Enter App name", type=str)
            data = {'name': app_name, 'app_platform': app_platform}
            if app_platform == 1:
                package_name = click.prompt("Enter Package name", type=str)
                data['package_name'] = package_name
            else:
                bundle_id = click.prompt("Enter Bundle Id", type=str)
                data['bundle_id'] = bundle_id

            resp = process_requests("POST", f"/projects/{proj_id}/apps/", data=data)
            if not resp:
                return
            return print_purple(f'{app_name} App created successfully')

        for k, v in app_dict[app_num].items():
            if k == 'app_id':
                continue
            click.echo(f'{k}: {v}')
        click.echo('')

        inp = click.prompt('What to do? \n 1 Modify \n 2 Delete', type=int)
        click.echo('')

        if inp == 1:
            name = click.prompt("Update app name", type=str)
            data = {'name': name}
            if app_dict[app_num].get('Package name'):
                p_name = app_dict[app_num]['Package name']
                package_name = click.prompt("Update package name", type=str, default=p_name)
                if package_name.strip():
                    data['package_name'] = package_name
                else:
                    data['package_name'] = p_name
            else:
                b_id = app_dict[app_num]['Bundle Id']
                bundle_id = click.prompt("Update bundle id name", type=str, default=b_id)
                if bundle_id.strip():
                    data['bundle_id'] = bundle_id
                else:
                    data['bundle_id'] = b_id

            app_id = app_dict[app_num]['app_id']
            resp = process_requests("PUT", f"/projects/{proj_id}/apps/{app_id}", data=data)
            app_name = resp.get('data')['name']
            print_purple(f'{app_name} App updated successfully')

        elif inp == 2:
            name = app_dict[app_num]['Name']
            confirm = click.prompt(f"Are you sure (Y or N) app {app_name}", type=str)
            if confirm.lower() == 'n':
                return
            app_id = app_dict[app_num]['app_id']
            resp = process_requests("DELETE", f"/projects/{proj_id}/apps/{app_id}")
            print_purple(f'{app_name} App deleted successfully')
        else:
            return

    except Exception:
        click.echo('Quit')
