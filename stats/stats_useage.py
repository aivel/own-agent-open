import os
from time import sleep

from stats.google_drive_api import GoogleDriveAPI
from stats.google_gsuite_api import GoogleGsuiteAPI
from stats.server_api import ServerAPI
import datetime

api_url = 'http://localhost:9092/{method_name}'

drive_api = GoogleDriveAPI()
gsuite_api = GoogleGsuiteAPI()
server_api = ServerAPI(api_url)



# emails: array of emails ['email1@gmail.com', 'email2@gmail.com']


def create_file(file_name, emails):
    result = {}

    file = drive_api.create_file(file_name)

    result['file_id'] = file['id']
    result['permissions'] = []

    for email in emails:
        permission_result = drive_api.create_permission(file['id'], email)
        result['permissions'].append({
            'permission_id': permission_result.get('id'),
            'email': email
        })

    result['link'] = drive_api.get_file(file['id']).get('webViewLink')

    return result


# Two params: teams and work_name
# Teams example: [{ 'team_name': 'Team 1', 'file_id' 'google file id' }]
# Work_name: 'Some homework name'

def create_teams_chart(teams, work_name):
    data = []

    result = {
        'teams_pics': [],
        'overall_stats_pic': ''
    }

    teams_chart_data = {
        'labels': [],
        'datasets': [],
    }

    for team in teams:
        individual_team_chart = {
            'labels': [],
            'datasets': [],
        }

        file_id = team['file_id']

        activities = gsuite_api.get_activities(file_id)

        for activity in activities:
            event = activity.get('combinedEvent')
            event_dt = datetime.datetime.fromtimestamp(int(event['eventTimeMillis']) / 1000)
            dt = datetime.datetime(year=event_dt.year, month=event_dt.month, day=event_dt.day,
                                   hour=event_dt.hour, minute=event_dt.minute, second=int(event_dt.second / 10) * 10,
                                   microsecond=0)

            event['event_dt'] = dt

        activities.sort(key=lambda x: x['combinedEvent']['event_dt'])

        activities = [activity for activity in activities if
                      activity['combinedEvent']['primaryEventType'] == 'comment' or
                      activity['combinedEvent']['primaryEventType'] == 'edit']

        team_stat = {}

        for activity in activities:
            event = activity.get('combinedEvent')
            dt_str = event['event_dt'].strftime('%H:%M:%S')
            if team_stat.get(dt_str) is None:
                team_stat[dt_str] = {
                    'dt': event['event_dt'],
                    'counter': 0
                }

            team_stat[dt_str]['counter'] += 1

        now = datetime.datetime.now()
        temp_dt = (now - datetime.timedelta(minutes=15)).replace(second=0, microsecond=0)

        while temp_dt < now:
            dt_str = temp_dt.strftime('%H:%M:%S')
            if team_stat.get(dt_str) is None:
                team_stat[dt_str] = {
                    'dt': temp_dt,
                    'counter': 0
                }
            temp_dt = temp_dt + datetime.timedelta(seconds=10)

        result_team_stat = []
        for key, value in team_stat.items():
            result_team_stat.append({
                'time_str': key,
                'counter': value['counter'],
                'dt': value['dt']
            })

        result_team_stat.sort(key=lambda x: x['dt'])

        labels = [0]
        team_dataset = [0]

        for stat in result_team_stat:
            labels.append(stat['time_str'])
            team_dataset.append(stat['counter'])

        individual_team_chart['labels'] = labels
        individual_team_chart['datasets'].append({
            'label': '{team_name} number of changes'.format(team_name=team['team_name']),
            'data': team_dataset
        })

        teams_chart_data['labels'] = labels
        teams_chart_data['datasets'].append({
            'label': '{team_name} number of changes'.format(team_name=team['team_name']),
            'data': team_dataset
        })

        file_name = '{team_name} {work_name}.png'.format(team_name=team['team_name'], work_name=work_name)
        file_path = os.path.join(os.getcwd(), file_name)

        team_image = server_api.get_image(individual_team_chart, file_path)
        result['teams_pics'].append({
            'team_name': team['team_name'],
            'stats_pic': file_path
        })

    file_name = 'All teams {work_name}.png'.format(work_name=work_name)
    file_path = os.path.join(os.getcwd(), file_name)

    teams_image = server_api.get_image(teams_chart_data, file_path)

    sleep(5)

    result['overall_stats_pic'] = file_path

    return result


def check_need_push(file_id):
    activities = gsuite_api.get_activities(file_id)

    for activity in activities:
        event = activity.get('combinedEvent')
        event_dt = datetime.datetime.fromtimestamp(int(event['eventTimeMillis']) / 1000)
        event['event_dt'] = event_dt
        print(activity)

    activities.sort(key=lambda x: x['combinedEvent']['event_dt'])

    activities = [activity for activity in activities if
                  activity['combinedEvent']['primaryEventType'] == 'comment' or
                  activity['combinedEvent']['primaryEventType'] == 'edit']

    now = datetime.datetime.now()

    if len(activities) == 0:
        return True

    last_dt = activities[-1]['combinedEvent']['event_dt']

    print(now)
    print(last_dt)
    print(now - last_dt)

    if (now - last_dt > datetime.timedelta(seconds=30)):
        return True
    else:
        return False
