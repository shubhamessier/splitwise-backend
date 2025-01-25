# Splitwise Backend API

Simplified REST API for splitwise applications

## Live Deployment Link

- API Demo - https://splitwise-backend-2.onrender.com/

## Features

- Create users.
- Allows to Create groups and add users to them.
- Add expenses to a group with equal or percentage-based splitting.
- View outstanding balances for users in a group.

## Setup

1.  **Clone the repository**
2.  **Install dependencies:** `pip install -r requirements.txt`
3.  **Create a `.env` file** with the database connection string (see `.env.example`)
4.  **Build and Run Docker containers:** `docker-compose up --build`
5.  **Access the App:** `http://localhost:5000`

## API Endpoints

### Users

#### Create a User

- **Method:** `POST`
- **URL:** `/users`
- **Request Body:**
  ```json
  {
    "name": "User Name"
  }
  ```
- **Response (Success - 201 Created):**
  ```json
  {
    "message": "User created successfully",
    "user": {
      "id": 1, // ID assigned by the database
      "name": "User Name"
    }
  }
  ```
- **Response (Error - 400 Bad Request):**
  ```json
  {
    "message": "Bad request",
    "error": "Name is required"
  }
  ```

#### Get All Users

- **Method:** `GET`
- **URL:** `/users`
- **Response (Success - 200 OK):**
  ```json
  [
    {
      "id": 1,
      "name": "Alice"
    },
    {
      "id": 2,
      "name": "Bob"
    }
  ]
  ```

### Groups

#### Create a Group

- **Method:** `POST`
- **URL:** `/groups`
- **Request Body:**
  ```json
  {
    "name": "Group Name",
    "user_ids": [1, 2] // Array of user IDs already created
  }
  ```
- **Response (Success - 201 Created):**
  ```json
  {
    "message": "Group created successfully",
    "group": {
      "id": 1,
      "name": "Group Name",
      "users": [
        {
          "id": 1,
          "name": "Alice"
        },
        {
          "id": 2,
          "name": "Bob"
        }
      ]
    }
  }
  ```
- **Response (Error - 400 Bad Request):**
  ```json
  {
    "message": "Bad request",
    "error": "Group name is required"
  }
  ```
- **Response (Error - 404 Not Found):**
  ```json
  {
    "message": "Resource not found",
    "error": "User with id 99 not found"
  }
  ```

#### Get All Groups

- **Method:** `GET`
- **URL:** `/groups`
- **Response (Success - 200 OK):**

````json
[
     {
         "id": 1,
         "name": "Group Name",
         "users": [
           {
              "id":1,
               "name":"Alice"
           },
            {
              "id":2,
              "name":"Bob"
             }
        ]
     },
     {
         "id": 2,
          "name": "Group Name 2",
          "users": [
           {
              "id":2,
               "name":"Bob"
           },
            {
              "id":3,
              "name":"Charlie"
             }
         ]
     }
 ]



Get a Specific Group

 Method: GET

 URL: /groups/<int:group_id>

 Response (Success - 200 OK):


 {
      "id": 1,
         "name": "Group Name",
         "users": [
           {
              "id":1,
               "name":"Alice"
           },
            {
              "id":2,
              "name":"Bob"
             }
         ]
 }



Response (Error - 404 Not Found):


{
  "message": "Resource not found",
  "error": "Group with id 99 not found"
}




Expenses
Add an Expense

 Method: POST

 URL: /expenses

 Request Body (Equal Split):


 {
     "description": "Dinner",
     "amount": 50,
     "group_id": 1,
     "payer_id": 1,
     "split_type": "equal",
      "split_data": null
 }



Request Body (Percentage Split):


{
 "description": "Movie Tickets",
 "amount": 25,
 "group_id": 1,
 "payer_id": 2,
 "split_type": "percentage",
 "split_data": {
   "1": 70, //User id 1 owes 70 percent
   "2": 30 //User id 2 owes 30 percent
   }
}




Response (Success - 201 Created):


{
"message": "Expense added successfully",
 "expense": {
     "id": 1,
     "description": "Dinner",
     "amount": 50.0,
     "group_id": 1,
     "payer_id": 1,
     "split_type": "equal",
     "split_data": null,
     "date_added": "2024-11-28T12:00:00.123456"
 }
}




 Response (Success - 201 Created)(Percentage split):
 ```json
 {
 "message": "Expense added successfully",
 "expense": {
 "id": 2,
 "description": "Movie Tickets",
 "amount": 25.0,
 "group_id": 1,
 "payer_id": 2,
 "split_type": "percentage",
 "split_data": {
 "1": 70,
 "2": 30
 },
 "date_added": "2024-11-28T12:30:00.123456"
 }
 }




c

 Response (Error - 400 Bad Request):


```json
{
 "message": "Bad request",
 "error": "Missing required expense data"
}
````

Use code with caution.

    Response (Error - 404 Not Found):

{
"message": "Resource not found",
"error": "Group with id 99 not found"
}

````
*   **Note:**
*   `split_type` can be either `equal` or `percentage`.
*   For `equal` splits,  `split_data` must be null.
*   For `percentage` splits, `split_data` must be a JSON object where the keys are `user_ids` and values are the percentage of the expense each user is responsible for.

#### Get All Expenses

*   **Method:** `GET`
*   **URL:** `/expenses`
*   **Response (Success - 200 OK):**
```json
[
    {
       "id": 1,
       "description": "Dinner",
       "amount": 50.0,
       "group_id": 1,
       "payer_id": 1,
       "split_type": "equal",
       "split_data": null,
       "date_added": "2024-11-28T12:00:00.123456"
    },
     {
       "id": 2,
       "description": "Movie Tickets",
       "amount": 25.0,
       "group_id": 1,
       "payer_id": 2,
       "split_type": "percentage",
       "split_data": {
            "1": 70,
            "2": 30
            },
       "date_added": "2024-11-28T12:30:00.123456"
      }

]
````

### Balances

#### Get Group Balances

- **Method:** `GET`
- **URL:** `/groups/<int:group_id>/balances`
- **Response (Success - 200 OK):**

```json
{
  "balances": {
    "1": 10.0, // User 1 balance (positive if they are owed, negative if they owe)
    "2": -10.0 // User 2 balance
  }
}
```

- **Response (Error - 404 Not Found):**

```json
{
  "message": "Resource not found",
  "error": "Group with id 99 not found"
}
```
