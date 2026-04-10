// eslint-disable-next-line @typescript-eslint/triple-slash-reference
/// <reference path="../support/index.d.ts" />

describe('Unified chat smoke', () => {
	before(() => {
		cy.registerAdmin();
	});

	it('opens auth and lands in the main chat flow', () => {
		cy.loginAdmin();
		cy.visit('/');
		cy.get('#chat-search').should('exist');
		cy.get('#chat-input').should('exist');
	});
});
