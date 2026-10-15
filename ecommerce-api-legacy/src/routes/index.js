const express = require('express');
const { asyncHandler } = require('../middlewares/asyncHandler');
const { adminAuth } = require('../middlewares/adminAuth');

function buildRoutes({ checkoutController, reportController, userController }, config) {
    const router = express.Router();

    router.post('/checkout', asyncHandler(async (req, res) => {
        res.status(200).json(await checkoutController.checkout(req.body));
    }));

    router.get('/admin/financial-report', adminAuth(config), asyncHandler(async (req, res) => {
        res.json(await reportController.financialReport());
    }));

    router.delete('/users/:id', asyncHandler(async (req, res) => {
        res.send(await userController.delete(req.params.id));
    }));

    return router;
}

module.exports = { buildRoutes };
