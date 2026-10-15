const { PaymentStatus } = require('../models/paymentModel');

const TABLES = [
    'CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name TEXT, email TEXT, pass TEXT)',
    'CREATE TABLE IF NOT EXISTS courses (id INTEGER PRIMARY KEY, title TEXT, price REAL, active INTEGER)',
    'CREATE TABLE IF NOT EXISTS enrollments (id INTEGER PRIMARY KEY, user_id INTEGER, course_id INTEGER)',
    'CREATE TABLE IF NOT EXISTS payments (id INTEGER PRIMARY KEY, enrollment_id INTEGER, amount REAL, status TEXT)',
    'CREATE TABLE IF NOT EXISTS audit_logs (id INTEGER PRIMARY KEY, action TEXT, created_at DATETIME)',
];

const SEED_USER = { name: 'Leonan', email: 'leonan@fullcycle.com.br', password: '123' };
const SEED_COURSES = [
    { title: 'Clean Architecture', price: 997.0 },
    { title: 'Docker', price: 497.0 },
];

async function initSchema(db, { hashPassword }) {
    for (const ddl of TABLES) await db.run(ddl);

    const { count } = await db.get('SELECT COUNT(*) AS count FROM courses');
    if (count > 0) return;

    await db.transaction(async () => {
        const passwordHash = await hashPassword(SEED_USER.password);
        const user = await db.run('INSERT INTO users (name, email, pass) VALUES (?, ?, ?)', [SEED_USER.name, SEED_USER.email, passwordHash]);
        const courseIds = [];
        for (const course of SEED_COURSES) {
            const { lastID } = await db.run('INSERT INTO courses (title, price, active) VALUES (?, ?, 1)', [course.title, course.price]);
            courseIds.push(lastID);
        }
        const enrollment = await db.run('INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)', [user.lastID, courseIds[0]]);
        await db.run('INSERT INTO payments (enrollment_id, amount, status) VALUES (?, ?, ?)', [enrollment.lastID, SEED_COURSES[0].price, PaymentStatus.PAID]);
    });
}

module.exports = { initSchema };
