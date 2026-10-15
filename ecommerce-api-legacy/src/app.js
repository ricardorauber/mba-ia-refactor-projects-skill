const express = require('express');
const settings = require('./config/settings');
const logger = require('./utils/logger');
const { createDatabase } = require('./database/connection');
const { initSchema } = require('./database/schema');
const { UserModel } = require('./models/userModel');
const { CourseModel } = require('./models/courseModel');
const { EnrollmentModel } = require('./models/enrollmentModel');
const { PaymentModel } = require('./models/paymentModel');
const { AuditLogModel } = require('./models/auditLogModel');
const { ReportModel } = require('./models/reportModel');
const { PaymentService } = require('./services/paymentService');
const passwordHasher = require('./services/passwordHasher');
const { CheckoutController } = require('./controllers/checkoutController');
const { ReportController } = require('./controllers/reportController');
const { UserController } = require('./controllers/userController');
const { buildRoutes } = require('./routes');
const { errorHandler } = require('./middlewares/errorHandler');

// Composition root: the only place that knows every concrete implementation.
async function createApp(config = settings) {
    const db = createDatabase(config.databasePath);
    await initSchema(db, passwordHasher);

    const userModel = new UserModel(db);
    const controllers = {
        checkoutController: new CheckoutController({
            transaction: (work) => db.transaction(work),
            userModel,
            courseModel: new CourseModel(db),
            enrollmentModel: new EnrollmentModel(db),
            paymentModel: new PaymentModel(db),
            auditLogModel: new AuditLogModel(db),
            paymentService: new PaymentService({ gatewayKey: config.paymentGatewayKey }),
            passwordHasher,
        }),
        reportController: new ReportController({ reportModel: new ReportModel(db) }),
        userController: new UserController({ userModel }),
    };

    const app = express();
    app.use(express.json());
    app.use('/api', buildRoutes(controllers, config));
    app.use(errorHandler);
    return { app, db };
}

if (require.main === module) {
    createApp(settings)
        .then(({ app }) => {
            app.listen(settings.port, settings.host, () => logger.info(`LMS API rodando na porta ${settings.port}`));
        })
        .catch((error) => {
            logger.error(`Falha ao iniciar a aplicação: ${error.stack || error}`);
            process.exit(1);
        });
}

module.exports = { createApp };
