import os.path
from tkinter import *
import requests
import json
import re
import threading


def get_latest_images(image_url):
    res = requests.get(image_url)

    if res.status_code == 200:
        response = json.loads(res.text)
        status_lbl.config(text="Writing new image data to json file...")
        with open(file_name, 'w', encoding="utf-8") as file:
            json.dump(response, file, ensure_ascii=False, indent=4)
            status_lbl.config(text="Data written to JSON file successfully.")


def get_latest_bulk_data(thread_lock):
    thread_lock.acquire()
    bulk_data_url = "https://api.scryfall.com/bulk-data"

    res = requests.get(bulk_data_url)
    status_lbl.config(text="Attempting to retrieve new image data...")
    if res.status_code == 200:
        response = json.loads(res.text)
        # Get the response for the "Unique Artwork" url
        download_url = response['data'][1]['download_uri']
        get_latest_images(download_url)

    thread_lock.release()


def get_images_for_requested_card(card_name):

    deck_name = "My Deck"

    if deck_name_input.index("end") != 0:
        deck_name = deck_name_input.get()

    data = {}

    full_directory_path = os.getcwd() + "/images/" + deck_name

    with open(file_name, 'rb') as file:
        data = json.load(file)

    status_lbl.config(text="Retrieved card data...")

    # List to hold basic land types to check against
    # to make sure we retrieve basic lands only once
    land_types = []

    for card in data:
        if card['name'] == card_name:
            get_card = True

            if "Basic Land" in card['type_line'] and card['type_line'] in land_types:
                get_card = False

            if get_card:
                image_uri = card['image_uris']['normal']
                res = requests.get(image_uri)
                status_lbl.config(text="Attempting to retrieve " + card_name + "image...")
                if res.status_code == 200:
                    status_lbl.config(text="Got image for " + card_name + ", writing to file")
                    if not os.path.exists(full_directory_path):
                        os.makedirs(full_directory_path)
                    with open(os.getcwd() + "/images/" + deck_name + "/" + card_name + ".jpg", 'wb') as file:
                        file.write(requests.get(image_uri).content)

                    if "Basic Land" in card['type_line'] and card['type_line'] not in land_types:
                        land_types.append(card['type_line'])


def submit_cards(thread_lock):
    thread_lock.acquire()

    status_lbl.config(text="Reading in card list...")
    inp = input_txt.get(1.0, "end")

    # Strip parentheses and descriptors from the string
    inp = re.sub(r'\([^)]*\)', '', inp)

    # Strip decimal numbers from the string
    inp = re.sub(r'\d+', '', inp)

    # Separate each card into its own line
    card_list = inp.split("\n")

    for card in card_list:
        # Strip leading and trailing spaces from the card name
        card = card.strip()

        # Strip hyphens and anything following them from the card name
        card = re.sub(r'\s*-\s*.*$', '', card)
        if card != '':
            get_images_for_requested_card(card)

    status_lbl.config(text="Finished!")
    thread_lock.release()


def start_card_submit():
    submit_cards_thread.start()


def start_get_card_data():
    get_card_data_thread.start()


# Set up multithreading
lock = threading.Lock()

submit_cards_thread = threading.Thread(target=submit_cards, args=(lock,))
get_card_data_thread = threading.Thread(target=get_latest_bulk_data, args=(lock,))

file_name = "latest_card_data.json"

# create root window
root = Tk()
root.title("MTG Card Image Retriever")
root.geometry('400x500')

# Create label
Label(root, text="Enter your cards here:").pack()

# adding Text Field
input_txt = Text(root, height=15, width=40)
input_txt.pack()

Label(root, text="Deck Name:").pack(pady=5)
deck_name_input = Entry(root, width=50)
deck_name_input.pack( padx=(0, 10))
Button(root, text="Submit cards", command=start_card_submit).pack(pady=8)
Button(root, text="Update card data", command=start_get_card_data).pack()

Label(root, text="Status:").pack(side=LEFT, padx=(5,0))
status_lbl = Label(root, height=15, width=40, bg="white")
status_lbl.pack(pady=8, padx=(0, 20))

# Execute Tkinter
root.mainloop()
