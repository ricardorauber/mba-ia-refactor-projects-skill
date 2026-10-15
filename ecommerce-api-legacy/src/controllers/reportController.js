class ReportController {
    constructor({ reportModel }) {
        this.reportModel = reportModel;
    }

    financialReport() {
        return this.reportModel.financialReport();
    }
}

module.exports = { ReportController };
