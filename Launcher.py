# main.py

import Code_indexer
import Search_Engine

while True:

    print("\n1. Build Index")
    print("2. Search")
    print("3. Exit")

    choice = input("Choice: ")

    if choice == "1":

        Code_indexer.build_index()

    elif choice == "2":

        Search_Engine.search()

    elif choice == "3":

        break

    else:
        print("Invalid choice")