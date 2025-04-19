# NL-to-SQL Agent

An interactive web application that converts **natural language questions** into **SQL queries** and executes them on user-uploaded SQLite databases. powered by **LangChain**, **FastAPI**, and **Streamlit**.

---

## Features

* Conversational chat interface to query DB data in natural language
* Multi-chat support with chat memory isolation, to upload multiple DBs in different chats and query each DB separately
* LLM generated SQL query and Top 10 rows returned as a dataframe for each natural language query
* Persistent chat memory across multiple chats stored as JSON files (supports future integration with Postgres, MongoDB etc.)
* Error handling for incorrect/ failed SQL queries

---

## Tech Stack
- **Python** for project design
- **LangChain** to build the re-act agent and to allow tool execution
- **Langsmith** to trace LLM calls
- **FastAPI** for the backend service
- **Streamlit** for quick UI generation

---

## Instructions to run the project

### With python installed

#### Clone the repository
```
git clone https://github.com/shreyas0511/NL-to-SQL.git
```

#### Navigate to the project folder
```
cd NL-to-SQL
```

#### Install dependencies
```
pip install --no-deps -r requirements.txt
```

#### Get a gemini API key from google AI studio and Langsmith API key for tracing LLM calls and store them in a **.env** file

```
GOOGLE_API_KEY = <YOUR_GOOGLE_API_KEY>
LANGSMITH_API_KEY = <YOUR_LANGSMITH_API_KEY>
```

#### Run the FastAPI backend first
```
uvicorn main:app --reload
```
#### FastAPI server now runs on http://localhost:8000

To directly test the api with FastAPI Swagger UI go to http://localhost:8000/docs

#### On a new terminal, run the Streamlit frontend
```
streamlit run app.py
```
#### The frontend will now be visible at http://localhost:8051


### Docker build coming soon ...


## Usage

#### With the app running, click “➕ New Chat” in the sidebar,  upload your SQLite **.db** file and start talking to your data.

I used the ChinookDB database for testing which contains digital media store data. This database can be found here: https://github.com/lerocha/chinook-database

#### Ask natural language questions like:

```
Show me the total number of albums per artist. Return the artist name and total
```

#### The agent returns:

```
🤖 Successfully executed the query, returned 204 rows

🧾 Executed Query:
SELECT ar.Name, count(al.AlbumId) AS TotalAlbums FROM Artist AS ar INNER JOIN Album AS al ON ar.ArtistId = al.ArtistId GROUP BY ar.ArtistId

📊 Top 10 Rows:
                   Name  count(al.AlbumId)
0                 AC/DC                  2
1                Accept                  2
2             Aerosmith                  1
3     Alanis Morissette                  1
4       Alice In Chains                  1
5  Antônio Carlos Jobim                  2
6          Apocalyptica                  1
7            Audioslave                  3
8              BackBeat                  1
9          Billy Cobham                  1
```

#### Chat history is retained, so you can also ask follow up questions related to previous questions like:

```
Sort them in descending order
```
#### The agent returns (with respect to the previous query):

```
🤖 Successfully executed the query, returning the artist name and the total number of albums they have, sorted in descending order.

🧾 Executed Query:
SELECT ar.Name, count(al.AlbumId) AS total FROM Artist AS ar INNER JOIN Album AS al ON ar.ArtistId = al.ArtistId GROUP BY ar.Name ORDER BY total DESC

              Name  total
0      Iron Maiden     21
1     Led Zeppelin     14
2      Deep Purple     11
3               U2     10
4        Metallica     10
5    Ozzy Osbourne      6
6        Pearl Jam      5
7  Various Artists      4
8        Van Halen      4
9             Lost      4
```


## Demo

#### A short video walkthrough of the project will be added here soon ...

