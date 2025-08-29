from backend.add_student import add_student
from backend.view_students import view_students

def main_menu():
    while True:
        print("\n=== Hostel Management Menu ===")
        print("1. Add Student")
        print("2. View Students")
        print("3. Exit")
        choice = input("Enter choice: ")

        if choice == "1":
            name = input("Enter student name: ")
            room = input("Enter room number: ")
            add_student(name, room)
        elif choice == "2":
            view_students()
        elif choice == "3":
            print("Exiting...")
            break
        else:
            print("Invalid choice. Try again.")

if __name__ == "__main__":
    main_menu()
