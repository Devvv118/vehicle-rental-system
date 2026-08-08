# Car Rental Management System

A full stack web app for managing a car rental business - customers, vehicles, rentals, reservations, maintenance, the whole thing. Built this to get more comfortable with FastAPI and React/TypeScript together, ended up being a much bigger project than I originally planned lol.

## What it does

Basically handles everything a rental company would need day to day:

- Customer management (with membership tiers and points)
- Vehicle fleet tracking, availability, maintenance history
- Reservations that check for date conflicts before booking
- Active rentals with return processing (late fees, damage fees, mileage tracking)
- Payment records
- Incident reports for accidents/damage
- Maintenance scheduling for the fleet
- A dashboard with basic revenue/stats

It's not connected to any payment gateway or anything, this was more about getting the data modeling and CRUD flows right across a decently complex schema.

## Tech stack

Backend
- FastAPI
- SQLAlchemy
- MySQL
- Pydantic for validation

Frontend
- React + TypeScript (Vite)
- React Router
- Plain CSS, no UI library

## Project structure

```
backend/
  models.py       sqlalchemy models
  schema.py       pydantic schemas  
  crud.py         db operations
  database.py     engine/session setup
  main.py         all the api routes

frontend/
  src/
    types/        typescript interfaces
    services/      api calls
    components/
    pages/
```

Database has around 15 tables - customers, vehicles, rentals, reservations, payments, employees, locations, maintenance records, insurance plans, incident reports etc, all wired together with foreign keys.

## Running it locally

You'll need MySQL running somewhere and Python + Node installed.

### Backend

First run the schema.sql file in MySQL workbench (or whatever client) to create the database and tables.

Then:

```
cd backend
pip install -r requirements.txt
```

Make a `.env` file with your db connection string

```
DATABASE_URL=mysql+pymysql://user:password@localhost:3306/car_rental
```

Start the server

```
uvicorn main:app --reload
```

Should be running on localhost:8000, you can check the auto generated docs at localhost:8000/docs

### Frontend

```
cd frontend
npm install
npm run dev
```

Runs on localhost:5173 by default.

Note - if you hit CORS errors, you'll need to add the CORS middleware to main.py pointing at your frontend url.

## A few things I learned / would do differently

Honestly the hardest part wasn't the CRUD stuff, it was figuring out the return flow for rentals - when a car comes back you have to calculate late fees if its overdue, log any damage, update mileage on the vehicle, mark it available again, and update the customer's membership points, all more or less at once. Getting that logic in one place instead of scattered around took a couple tries.

If I kept working on this I'd probably add:
- actual auth (right now anyone can hit any endpoint, not great)
- tests, there are none right now which is bad
- some kind of notification system for overdue rentals / upcoming maintenance
- better handling of concurrent bookings on the same vehicle

## Sample data

There's a small sql snippet in the setup docs to seed a couple customers/vehicles/locations if you want to poke around without creating everything by hand.

---

Built as a learning project, not meant for production use as is.
