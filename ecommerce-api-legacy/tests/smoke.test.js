// Run with: node --test tests/
const { test, before, after } = require('node:test');
const assert = require('node:assert/strict');
const { spawn } = require('node:child_process');
const fs = require('node:fs');
const net = require('node:net');
const os = require('node:os');
const path = require('node:path');

const ADMIN_TOKEN = 'smoke-test-token';
const REPORT = '/api/admin/financial-report';
let server;
let base;
let workdir;

function freePort() {
    return new Promise((resolve) => {
        const srv = net.createServer().listen(0, '127.0.0.1', () => {
            const { port } = srv.address();
            srv.close(() => resolve(port));
        });
    });
}

function call(method, urlPath, { body, headers = {} } = {}) {
    return fetch(base + urlPath, {
        method,
        headers: { 'Content-Type': 'application/json', ...headers },
        body: body === undefined ? undefined : JSON.stringify(body),
    });
}

before(async () => {
    const port = await freePort();
    workdir = fs.mkdtempSync(path.join(os.tmpdir(), 'lms-smoke-'));
    base = `http://127.0.0.1:${port}`;
    server = spawn(process.execPath, ['src/app.js'], {
        cwd: path.join(__dirname, '..'),
        env: {
            ...process.env,
            PORT: String(port),
            HOST: '127.0.0.1',
            DATABASE_PATH: path.join(workdir, 'smoke.db'),
            ADMIN_TOKEN,
            PAYMENT_GATEWAY_KEY: 'smoke-gateway-key',
            LOG_LEVEL: 'silent',
        },
        stdio: 'inherit',
    });
    for (let i = 0; i < 50; i++) {
        try { await fetch(base + '/'); return; } catch { await new Promise((r) => setTimeout(r, 200)); }
    }
    throw new Error('server did not start');
});

after(() => {
    server.kill();
    fs.rmSync(workdir, { recursive: true, force: true });
});

test('admin report requires the admin token', async () => {
    assert.equal((await call('GET', REPORT)).status, 401);
    assert.equal((await call('GET', REPORT, { headers: { 'X-Admin-Token': 'wrong' } })).status, 403);
});

test('admin report with the token returns the seeded courses', async () => {
    const res = await call('GET', REPORT, { headers: { 'X-Admin-Token': ADMIN_TOKEN } });
    assert.equal(res.status, 200);
    const report = await res.json();
    assert.deepEqual(report.map((c) => c.course), ['Clean Architecture', 'Docker']);
    assert.deepEqual(Object.keys(report[0]), ['course', 'revenue', 'students']);
    assert.deepEqual(report[0].students, [{ student: 'Leonan', paid: 997 }]);
});

test('checkout succeeds for a new and an existing user', async () => {
    const created = await call('POST', '/api/checkout', {
        body: { usr: 'Guilherme', eml: 'gui@fullcycle.com.br', pwd: 'senhaforte', c_id: 2, card: '4111222233334444' },
    });
    assert.equal(created.status, 200);
    assert.deepEqual(Object.keys(await created.json()), ['msg', 'enrollment_id']);

    const existing = await call('POST', '/api/checkout', {
        body: { usr: 'Leonan', eml: 'leonan@fullcycle.com.br', pwd: '123', c_id: 2, card: '4111222233334444' },
    });
    assert.equal(existing.status, 200);
});

test('checkout rejects denied payments, missing fields and unknown courses', async () => {
    const denied = await call('POST', '/api/checkout', {
        body: { usr: 'João', eml: 'joao@teste.com', pwd: '123', c_id: 1, card: '5111222233334444' },
    });
    assert.equal(denied.status, 400);
    assert.equal(await denied.text(), 'Pagamento recusado');

    assert.equal((await call('POST', '/api/checkout', { body: { usr: 'X', eml: 'x@x.com' } })).status, 400);
    assert.equal((await call('POST', '/api/checkout', { body: { usr: 'X', eml: 'x@x.com', c_id: 999, card: '4111' } })).status, 404);
});

test('invalid input answers 400 without leaking a stack trace', async () => {
    const malformed = await fetch(base + '/api/checkout', {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: '{bad',
    });
    assert.equal(malformed.status, 400);
    assert.doesNotMatch(await malformed.text(), /at |SyntaxError/);

    const objectCard = await call('POST', '/api/checkout', { body: { usr: 'X', eml: 'x@x.com', c_id: 1, card: { n: 4 } } });
    assert.equal(objectCard.status, 400);
});

test('report reflects the checkouts', async () => {
    const res = await call('GET', REPORT, { headers: { 'X-Admin-Token': ADMIN_TOKEN } });
    const docker = (await res.json()).find((c) => c.course === 'Docker');
    assert.equal(docker.revenue, 994);
    assert.equal(docker.students.length, 2);
});

test('deleting a user also removes their enrollments and payments', async () => {
    assert.equal((await call('DELETE', '/api/users/1')).status, 200);
    const res = await call('GET', REPORT, { headers: { 'X-Admin-Token': ADMIN_TOKEN } });
    const students = (await res.json()).flatMap((c) => c.students.map((s) => s.student));
    assert.deepEqual(students, ['Guilherme']);
});
