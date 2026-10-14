
print()
print()
print("================================================")
print()
print("        WELCOME TO POCKET TRACK 💸 !!")
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

            try:
                amount = float(data[1])
                expenses.append([expense_name, amount])
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

        expense_name = input("What did you spend on? huh...: ").strip()

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

        # ADD TO LIST

        expenses.append([expense_name, amount])

        # SAVE TO FILE

        file = open("expenses.txt", "a")
        file.write(expense_name + "," + str(amount) + "\n")
        file.close()

        print()
        print("Purchase logged:", expense_name)
        print("Amount: ₹", amount)
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
                print(expense[0], "- ₹", expense[1])

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
