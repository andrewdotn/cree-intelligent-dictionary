context('Word details', () => {
  describe('I want to see the word class and inflectional category for a Cree word', () => {
    // Test at least one word from each word class:
    //
    const testCases = [
      {wc: 'VTA', ic: 'VTA-1', word: 'mowêw'},
      {wc: 'VAI', ic: 'VAI-v', word: 'wâpiw'},
      {wc: 'VTI', ic: 'VTI-3', word: 'mîciw'},
      {wc: 'VII', ic: 'VII-n', word: 'nîpin'},
      {wc: 'NAD', ic: 'NDA-1', word: 'nôhkom'},
      {wc: 'NID', ic: 'NDI-1', word: 'mîpit'},
      {wc: 'NA',  ic: 'NA-1', word: 'minôs'},
      {wc: 'NI',  ic: 'NI-2', word: 'nipiy'},
      {wc: 'IPC', ic: null, word: 'ispîhk'},
    ]

    // Create test cases for each word above
    for (let {wc, word, ic} of testCases) {
      it(`should display the word class and inflection class for ${word} (${wc})`, () => {
        cy.visitLemma(word)

        cy.url()
          .should('contain', 'word/')

        cy.get('[data-cy=elaboration]')
          .contains(wc)

        if (!ic)
          return

        cy.get('[data-cy=elaboration]')
          .contains(ic)
      })
    }
  })
})
