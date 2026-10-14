
from datetime import datetime

print()
print()
print("================================================")
print()
print("       WELCOME TO POCKET TRACK 💸 !!")
print("     because, bro needs to stop being broke...")
print("       Let's see where the money disappears ")
print()

expenses = []

# LOAD OLD EXPENSES

try:
    file = open("expenses.txt", "r")

    for line in file:
        data = line.strip().split(",")

        if len(data) == 2:
            expense_name = data[0]
            expense_date = ""

            try:
                amount = float(data[1])
                expenses.append([expense_name, amount, expense_date])
            except ValueError:
                continue

        elif len(data) == 3:
            expense_name = data[0]
            expense_date = data[2]

            try:
                amount = float(data[1])
                expenses.append([expense_name, amount, expense_date])
            except ValueError:
                continue

    file.close()

except FileNotFoundError:
    file = open("expenses.txt", "w")
    file.close()


# MAIN MENU

while True:
    print("========= POCKETTRACK: WALLET CHECK 💳 =========")
    print()
    print("1. Add an expense")
    print("2. View expenses")
    print("3. View total spending")
    print("4. Exit")
    print()

    choice = input("Choose your move (1-4): ")

    # ADD EXPENSE

    if choice == "1":
        print("------------------------------------------------")
        print()
        print("FINANCIAL DAMAGE CHECKKKK 😭")
        print()

        expense_name = input(
            "What did you spend on? huh...: "
        ).strip()

        if expense_name == "" or "," in expense_name:
            print("Brooo 😭 enter a name without commas!")
            continue

        try:
            amount = float(input("Drop the amount ₹: "))

            if amount <= 0:
                print("Brooo 😭 amount must be greater than zero!")
                continue

        except ValueError:
            print("Numbers only, yawr! 😭 Try again.")
            continue

        # GET CURRENT DATE

        expense_date = datetime.now().strftime("%d-%m-%Y")

        # ADD TO LIST

        expenses.append([expense_name, amount, expense_date])

        # SAVE TO FILE

        file = open("expenses.txt", "a")
        file.write(
            expense_name + "," + str(amount) + "," + expense_date + "\n"
        )
        file.close()

        print()
        print("Purchase logged:", expense_name)
        print("Amount: ₹", amount)
        print("Date:", expense_date)
        print("Expense saved successfully! 💸")

    # VIEW EXPENSES

    elif choice == "2":
        print()
        print("========= YOUR EXPENSES 📋 =========")
        print()

        if len(expenses) == 0:
            print("No expenses yet. Go spend... responsibly 😭")

        else:
            for expense in expenses:
                if expense[2]:
                    print(
                        expense[0],
                        "- ₹", expense[1],
                        "- Date:", expense[2]
                    )
                else:
                    print(
                        expense[0],
                        "- ₹", expense[1],
                        "- Date unavailable"
                    )

    # VIEW TOTAL SPENDING

    elif choice == "3":
        print()
        print("========= TOTAL DAMAGE 💸 =========")
        print()

        total = 0

        for expense in expenses:
            total = total + expense[1]

        print("Total money disappeared: ₹", round(total, 2))

    # EXIT

    elif choice == "4":
        print()
        print("BYEEE 👋")
        print("Stop spending. Start surviving. 😛💸")
        break

    # INVALID MENU CHOICE

    else:
        print("Invalid choice!!! Choose 1-4.")

    print()
    print()
