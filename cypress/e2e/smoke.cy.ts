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

	it('shows unified chat orchestration controls and memory panel', () => {
		cy.loginAdmin();
		cy.visit('/');
		cy.get('[data-testid="chat-mode-switch"]').should('exist');
		cy.get('[data-testid="chat-model-selector"]').should('exist');
		cy.get('[data-testid="chat-upload-button"]').should('exist');
		cy.get('[data-testid="chat-url-button"]').should('exist');
		cy.get('[data-testid="chat-voice-button"]').should('exist');
		cy.get('[data-testid="chat-research-toggle"]').should('exist');
		cy.get('[data-testid="chat-memory-toggle"]').should('exist');
		cy.get('[data-testid="chat-safe-mode-toggle"]').should('exist');
		cy.get('[data-testid="chat-memory-panel-toggle"]').click();
		cy.get('[data-testid="memory-panel"]').should('be.visible');
	});
});
