import sqlite3
from mcp.server.fastmcp import FastMCP

server = FastMCP("job-tracker")

# Database setup
def get_db():
    conn = sqlite3.connect("jobs.db")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS roles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company TEXT NOT NULL,
            title TEXT NOT NULL,
            url TEXT,
            status TEXT DEFAULT 'interested',
            date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company TEXT NOT NULL,
            note TEXT NOT NULL,
            date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

init_db()

# Tools

@server.tool()
def add_role(company: str, title: str, url: str = "", status: str = "interested") -> str:
    """Add a job role to the pipeline. Status can be: interested, applied, interviewing, offer, rejected."""
    conn = get_db()
    conn.execute(
        "INSERT INTO roles (company, title, url, status) VALUES (?, ?, ?, ?)",
        (company, title, url, status)
    )
    conn.commit()
    conn.close()
    return f"Added {title} at {company} with status '{status}'"

@server.tool()
def get_pipeline() -> str:
    """Get all roles in the job pipeline, grouped by status."""
    conn = get_db()
    rows = conn.execute("SELECT company, title, status, url, date_added FROM roles ORDER BY status, date_added DESC").fetchall()
    conn.close()
    if not rows:
        return "Pipeline is empty. Add roles with add_role."
    result = ""
    current_status = ""
    for row in rows:
        if row["status"] != current_status:
            current_status = row["status"]
            result += f"\n--- {current_status.upper()} ---\n"
        result += f"  {row['company']} — {row['title']}"
        if row["url"]:
            result += f" ({row['url']})"
        result += f" [added {row['date_added']}]\n"
    return result

@server.tool()
def update_status(company: str, new_status: str) -> str:
    """Update the status of a role. Status options: interested, applied, interviewing, offer, rejected."""
    conn = get_db()
    cursor = conn.execute(
        "UPDATE roles SET status = ? WHERE company = ?",
        (new_status, company)
    )
    conn.commit()
    count = cursor.rowcount
    conn.close()
    if count == 0:
        return f"No roles found for '{company}'"
    return f"Updated {count} role(s) at {company} to '{new_status}'"

@server.tool()
def add_note(company: str, note: str) -> str:
    """Add a research note about a company."""
    conn = get_db()
    conn.execute(
        "INSERT INTO notes (company, note) VALUES (?, ?)",
        (company, note)
    )
    conn.commit()
    conn.close()
    return f"Note added for {company}"

@server.tool()
def get_notes(company: str) -> str:
    """Get all research notes for a company."""
    conn = get_db()
    rows = conn.execute(
        "SELECT note, date_added FROM notes WHERE company = ? ORDER BY date_added DESC",
        (company,)
    ).fetchall()
    conn.close()
    if not rows:
        return f"No notes found for {company}"
    result = f"Notes for {company}:\n"
    for row in rows:
        result += f"  [{row['date_added']}] {row['note']}\n"
    return result

if __name__ == "__main__":
    server.run(transport="stdio")