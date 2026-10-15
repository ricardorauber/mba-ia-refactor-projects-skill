class UserController {
    constructor({ userModel }) {
        this.userModel = userModel;
    }

    async delete(id) {
        await this.userModel.deleteWithRelations(id);
        return 'Usuário deletado, junto com suas matrículas e pagamentos.';
    }
}

module.exports = { UserController };
