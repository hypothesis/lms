import { documentCFI, stripCFIAssertions } from '../cfi';

describe('cfi', () => {
  describe('stripCFIAssertions', () => {
    it('returns CFI without assertions unchanged', () => {
      assert.equal(stripCFIAssertions('/1/2/3/10'), '/1/2/3/10');
    });

    it('removes assertions from CFI', () => {
      assert.equal(stripCFIAssertions('/1/2[chap4ref]'), '/1/2');
      assert.equal(
        stripCFIAssertions('/1[part1ref]/2[chapter2ref]/3[subsectionref]'),
        '/1/2/3',
      );
    });

    it('ignores escaped characters', () => {
      assert.equal(stripCFIAssertions('/1/2[chap4^[ignoreme^]ref]'), '/1/2');
      assert.equal(stripCFIAssertions('/1/2[a^[b^]]/3[c^[d^]]'), '/1/2/3');
    });
  });

  describe('documentCFI', () => {
    it('returns part of CFI before first step indirection', () => {
      // Typical CFI with one step indirection.
      assert.equal(documentCFI('/2/4/8!/10/12'), '/2/4/8');

      // Rarer case of CFI with multiple step indirections.
      assert.equal(documentCFI('/2/4/8!/10/12!/2/4'), '/2/4/8');
    });

    it('strips assertions', () => {
      assert.equal(
        documentCFI('/6/152[;vnd.vst.idref=ch13_01]!/4/2[ch13_sec_1]'),
        '/6/152',
      );
    });
  });
});
