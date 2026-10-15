const sqlite3 = require('sqlite3');

// Promisified wrapper over one sqlite3 connection. Transactions are queued so
// two requests never open BEGIN on the same connection at the same time.
function createDatabase(path) {
    const raw = new sqlite3.Database(path);
    let queue = Promise.resolve();

    const db = {
        get: (sql, params = []) => new Promise((resolve, reject) => {
            raw.get(sql, params, (err, row) => (err ? reject(err) : resolve(row)));
        }),
        all: (sql, params = []) => new Promise((resolve, reject) => {
            raw.all(sql, params, (err, rows) => (err ? reject(err) : resolve(rows)));
        }),
        run: (sql, params = []) => new Promise((resolve, reject) => {
            raw.run(sql, params, function onRun(err) {
                return err ? reject(err) : resolve({ lastID: this.lastID, changes: this.changes });
            });
        }),
        transaction(work) {
            const result = queue.then(async () => {
                await db.run('BEGIN');
                try {
                    const value = await work();
                    await db.run('COMMIT');
                    return value;
                } catch (error) {
                    await db.run('ROLLBACK');
                    throw error;
                }
            });
            queue = result.catch(() => {});
            return result;
        },
    };
    return db;
}

module.exports = { createDatabase };
