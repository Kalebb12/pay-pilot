from google.genai import types
from sqlalchemy.orm import Session
from decimal import Decimal
from google import genai
from models import Expense
from models import User


genai_client = genai.Client()

onboard_user_decl = types.FunctionDeclaration(
    name="onboard_user",
    description="Set the user's starting balance when they first join",
    parameters={
        "type": "object",
        "properties": {
            "balance": {"type": "number", "description": "The user's starting balance in naira"}
        },
        "required": ["balance"]
    }
)

log_expense_decl = types.FunctionDeclaration(
    name="log_expense",
    description="Log one or more expenses the user mentioned spending money on",
    parameters={
        "type": "object",
        "properties": {
            "expenses": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "category": {"type": "string"},
                        "amount": {"type": "number"},
                        "description": {"type": "string"},
                        "is_capex": {"type": "boolean"}
                    },
                    "required": ["category", "amount", "description"]
                }
            }
        },
        "required": ["expenses"]
    }
)

get_status_decl = types.FunctionDeclaration(
    name="get_status",
    description="Get the user's burn rate, days until broke, and personal inflation rate",
    parameters={"type": "object", "properties": {}}
)

update_balance_decl = types.FunctionDeclaration(
    name="update_balance",
    description="Update balance directly, e.g. user received new money",
    parameters={
        "type": "object",
        "properties": {"balance": {"type": "number"}},
        "required": ["balance"]
    }
)

# Tool wraps a LIST of declarations
tools = [types.Tool(function_declarations=[
    onboard_user_decl, log_expense_decl, get_status_decl, update_balance_decl
])]

def build_system_prompt(user: User) -> str:
    if not user.onboarded:
        return """
You are Days Until Broke, a financial assistant on WhatsApp for Nigerian students.
This user is new and has not set their balance yet.
Your only job right now is to call onboard_user with their balance.
Ask them for it if they haven't provided it.
"""
    return f"""
You are Days Until Broke, a financial assistant on WhatsApp for Nigerian students.

User's current balance: ₦{user.balance:,.0f}
User is onboarded: True

Your job:
- If the user mentions spending money → call log_expense
- If the user asks for status, burn rate, or how long money will last → call get_status  
- If the user says they received money or wants to update balance → call update_balance
- Map ALL expenses to exactly one of these NBS categories:
  Food and Non-Alcoholic Beverages, Transport, Communication, Housing Water Electricity Gas and Other Fuel,
  Education, Health, Clothing and Footwear, Restaurants and Hotels,
  Furnishings and Household Equipment Maintenance, Recreation and Culture,
  Alcoholic Beverages Tobacco and Kola, Miscellaneous Goods and Services
- Flag is_capex True if amount >= ₦{user.balance * Decimal('0.20'):,.0f} (20% of balance) or item is rent/laptop/phone
"""

async def log_expense(db: Session, expenses, user):
  for ex in expenses:
    expense = Expense(
      category=ex["category"], 
      amount=ex["amount"],
      description=ex["description"],
      is_capex=ex["is_capex"],
      phone_number=user.phone_number
    )
    db.add(expense)
    user.balance -= expense.amount
  db.commit()
  return "Expense logged successfully"
     
   
async def onboard_user(db: Session, balance, user):
  user.balance = balance
  user.onboarded = True
  db.commit()
  return "user updated successfully"
  

async def get_status(db: Session, user):
   return "Still in progress!!"
async def update_balance(db: Session, balance, user):
   user.balance += balance
   db.commit()
   return "user updated successfully"

async def execute_function(db : Session, name, args, user):
    if name == "log_expense":
        return await log_expense(db, args["expenses"], user)
    elif name == "onboard_user":
        return await onboard_user(db, args["balance"], user)
    elif name == "get_status":
        return await get_status(db, user)
    elif name == "update_balance":
        return await update_balance(db, args["balance"], user)
    else:
        return "Sorry, I didn't understand that."
    

class Helpers:

  @staticmethod
  def get_or_create_user(db: Session, phone_no: str):
    user =  db.query(User).filter(User.phone_number == phone_no).first()
    if not user:
      user = User(phone_number=phone_no)
      db.add(user)
      db.commit()
      db.refresh(user)
    return user

  @staticmethod
  async def agent(db: Session, message: str, user: User) -> str:

    system_prompt = build_system_prompt(user)

    response = genai_client.models.generate_content(
      model = "gemini-3.1-flash-lite",
      contents=message,
      config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                tools=tools,
            )
    )

    candidate = response.candidates[0]
    for part in candidate.content.parts:
        if part.function_call:
            result = await execute_function(db, part.function_call.name, part.function_call.args, user)
            return result
        if part.text:
            return part.text
    return "Sorry i didn't get that."