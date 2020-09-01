import PySimpleGUI as sg
import pathlib
import pickle
import base64
from tqdl import download
import time
import pytz
from dateutil import parser
import httplib2

h = httplib2.Http()


def load_dct():
    with open("urls.pkl", 'rb') as input:
        decoded = bytes(input.read())
    decoded = base64.b64decode(decoded)
    return pickle.loads(decoded)


courses_dct = load_dct()


def selector():
    layout = [
        [sg.Text('Please enter your course id, course year, course semester')],
        [sg.Text('ID', size=(15, 1)), sg.InputText('80131', key='-ID-')],
        [sg.Text('Year', size=(15, 1)), sg.InputText('2018', key='-YEAR-'), sg.Text('Note: calendar year'
                                                                                    'which the academic year '
                                                                                    'starts\n for example: '
                                                                                    '2020 semester B is 2019')],
        [sg.Text('Semester', size=(15, 1)), sg.InputText('1', key='-SEMESTER-'), sg.Text('Semester A: 1, Semester B: 2'
                                                                                         'Semester Summer: Summer')],
        [sg.Submit(), sg.Cancel()]
    ]
    window = sg.Window('Course details', layout)
    return mainloop(window)


def mainloop(window):
    while True:
        event, values = window.read()
        if not event or event == "Cancel":
            sg.popup("Goodbye.")
            window.close()
            exit()
        id = values['-ID-']
        year = int(values['-YEAR-'])
        semester = f"Semester {values['-SEMESTER-']}"
        if (id, year, semester) in courses_dct:
            sg.popup(event, "Congratulations, we found your course! proceeding")
            window.close()
            return id, year, semester
        else:
            sg.popup(event, "Sorry, we can't find it")


def preferences(id, year, semester):
    checkboxes = []
    for course in courses_dct[(id, year, semester)]:
        checkboxes.append([sg.Checkbox(course, default=True, key=course)])
    layout = [
        [sg.Text('What do you want to download? How?', size=(30, 1), justification='center', font=("Helvetica", 25),
                 relief=sg.RELIEF_RIDGE)],
        [sg.Frame(layout=checkboxes, title='Folders', title_color='red', relief=sg.RELIEF_SUNKEN)],
        [sg.Text('Do you want the screen files? AKA presentations in the PC')],
        [sg.Radio('Yes', "SCREEN", key='-SCREEN-'), sg.Radio('No', "SCREEN", default=True)],
        [sg.Text('Do you want to download the files or simply the urls?')],
        [sg.Radio('Download', "URL", default=True), sg.Radio('URLS', "URL", key='-URL-')],
        [sg.Submit(tooltip='Click to submit this form'), sg.Cancel()]
    ]
    window = sg.Window("Choose your preferences", layout)
    while True:

        event, values = window.read()
        if not event or event == "Cancel":
            window.close()
            main()
        folder = sg.popup_get_folder("Where do you want to save this?")
        if folder:
            break
    window.close()
    return values, folder, id, year, semester


def downloader(values, folder, id, year, semester):
    for course, lessons in courses_dct[(id, year, semester)].items():
        if values['-URL-']:
            with open(rf"{folder}/{id} {year} {semester} {course}.txt", "w") as output:
                for lesson in lessons:
                    cam_url = lesson["PrimaryVideo"]
                    screen_url = lesson["SecondaryVideo"]
                    output.write(f"{cam_url}\n")
                    is_screen = True
                    resp = h.request(screen_url, 'HEAD')
                    if not int(resp[0]['status']) < 400:
                        is_screen = False
                    if values['-SCREEN-'] and is_screen:
                        output.write(f"{screen_url}\n")
            print("Check your Folder!")
            return
        for lesson in lessons:
            if not values[course]:
                continue
            print(folder)
            pathlib.Path(fr'{folder}\{course}').mkdir(parents=True, exist_ok=True)
            cam_url = lesson["PrimaryVideo"]
            screen_url = lesson["SecondaryVideo"]
            date_str = lesson['CreationDate']
            datetime_object = parser.parse(date_str)
            israel = pytz.timezone('Israel')
            date_local = israel.localize(datetime_object)
            dt = date_local.strftime('%Y-%m-%d %H-%M')
            title = f'{dt} {id}'
            print(dt)
            print(course)
            print(title)
            print(fr"Downloading... {folder}/{course}/{title}.mp4")
            download(cam_url, fr"{folder}/{course}/{title}.mp4")
            is_screen = True
            resp = h.request(screen_url, 'HEAD')
            if not int(resp[0]['status']) < 400:
                is_screen = False
            if values['-SCREEN-'] and is_screen:
                print(fr"Downloading... {folder}/{course}/{title} screen.mp4")
                download(screen_url, fr"{folder}/{course}/{title} screen.mp4")
        print("Check your Folder!")


def main():
    id, year, semester = selector()
    values, folder, id, year, semester = preferences(id, year, semester)
    downloader(values, folder, id, year, semester)
    time.sleep(2)


if __name__ == '__main__':
    main()