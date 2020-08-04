/**
 * @typedef {import('../api-types').Chapter} Chapter
 */

// Dummy book and chapter data for testing the book selection UI. This is
// extracted from the VitalSource Products API.
//
// See https://developer.vitalsource.com/hc/en-us/articles/360010967153-GET-v4-products-vbid-Title-TOC-Metadata.
//
// The book metadata comes from the `https://api/vitalsource.com/v4/products/{BOOK_ID}`
// response.
//
// The chapter metadata comes from the `https://api/vitalsource.com/v4/products/{BOOK_ID}/toc`
// response.

export const bookList = [
  {
    // Chosen from `https://api.vitalsource.com/v4/products` response.
    id: 'BOOKSHELF-TUTORIAL',
    title: 'Bookshelf Tutorial',
    cover_image:
      'https://covers.vitalbook.com/vbid/BOOKSHELF-TUTORIAL/width/480',
  },
  {
    // See https://github.com/hypothesis/product-backlog/issues/1200
    id: '9781400847402',
    title: '"T. rex" and the Crater of Doom',
    cover_image: 'https://covers.vitalbook.com/vbid/9781400847402/width/480',
  },
];

/** @type {Record<string, Chapter[]>} */
export const chapterData = {
  'BOOKSHELF-TUTORIAL': [
    {
      title: 'Cover',
      cfi: '/6/2[;vnd.vst.idref=vst-4b4cfacf-80a2-440c-acaf-70ed8fb158f1]',
      page: '1',
    },
    {
      title: 'Welcome!',
      cfi: '/6/4[;vnd.vst.idref=vst-ae169b91-f520-449d-b99c-655767e4d0a1]',
      page: '2',
    },
    {
      title: 'Welcome!',
      cfi: '/6/4[;vnd.vst.idref=vst-ae169b91-f520-449d-b99c-655767e4d0a1]',
      page: '2',
    },
    {
      title: 'Getting Started',
      cfi: '/6/6[;vnd.vst.idref=vst-1bc048d4-7e99-404a-bce8-5dda6038a042]',
      page: '3',
    },
    {
      title: 'Part 1: How Do I Access My Digital Content?',
      cfi: '/6/8[;vnd.vst.idref=vst-70a6f9d3-0932-45ba-a583-6060eab3e536]',
      page: '4',
    },
    {
      title: 'Part 1: How Do I Access My Digital Content?',
      cfi: '/6/8[;vnd.vst.idref=vst-70a6f9d3-0932-45ba-a583-6060eab3e536]',
      page: '4',
    },
    {
      title: 'Find an eBook in Your Learning Management System',
      cfi: '/6/10[;vnd.vst.idref=vst-353dae26-fc2c-4666-9f42-8780bbd7b96c]',
      page: '5',
    },
    {
      title: 'Redeem a Code for an eBook in Bookshelf',
      cfi: '/6/12[;vnd.vst.idref=vst-45af6392-b176-46e3-9f0c-0a083fc6103e]',
      page: '6',
    },
    {
      title: 'Video Demonstration: Redeeming a Code in Bookshelf Online',
      cfi: '/6/14[;vnd.vst.idref=vst-070d7be2-6463-4c3f-acf2-13dc00e25c3c]',
      page: '7',
    },
    {
      title: 'Access Content Through Bridge',
      cfi: '/6/16[;vnd.vst.idref=vst-4cf3e83d-8eba-4ebc-a35f-c999dc093d4c]',
      page: '8',
    },
    {
      title: 'Part 2: Create and Manage Your Bookshelf Account',
      cfi: '/6/18[;vnd.vst.idref=vst-510c9334-1807-4b2c-bb32-c45da93065ba]',
      page: '9',
    },
    {
      title: 'Part 2: Create and Manage Your Bookshelf Account',
      cfi: '/6/18[;vnd.vst.idref=vst-510c9334-1807-4b2c-bb32-c45da93065ba]',
      page: '9',
    },
    {
      title: 'Video Demonstration: Create Your Bookshelf Account',
      cfi: '/6/20[;vnd.vst.idref=vst-2e5f44ef-7fae-42fd-b326-a3e9989da503]',
      page: '10',
    },
    {
      title: 'Manage Your Bookshelf Account',
      cfi: '/6/22[;vnd.vst.idref=vst-75af51a6-e0c3-480a-8c09-54bf7680703d]',
      page: '11',
    },
    {
      title: 'Learning Check: Create and Manage Your Bookshelf Account',
      cfi: '/6/24[;vnd.vst.idref=vst-bb1fc8ec-16f4-43f8-931b-b384aea75dbc]',
      page: '12',
    },
    {
      title: 'Part 3: Download the Bookshelf Desktop and Mobile Apps',
      cfi: '/6/26[;vnd.vst.idref=vst-fbd8d78c-9094-4307-ad8c-4548ecb12672]',
      page: '13',
    },
    {
      title: 'Part 3: Download the Bookshelf Desktop and Mobile Apps',
      cfi: '/6/26[;vnd.vst.idref=vst-fbd8d78c-9094-4307-ad8c-4548ecb12672]',
      page: '13',
    },
    {
      title:
        'Video Demonstration: Downloading the Bookshelf Desktop Application',
      cfi: '/6/28[;vnd.vst.idref=vst-50dc1ebe-4bff-40b0-b343-8ffeac0ee79a]',
      page: '14',
    },
    {
      title: 'Part 4: Enhance Learning Experience with Bookshelf',
      cfi: '/6/30[;vnd.vst.idref=vst-4d80c0ec-c94b-4ade-956c-c7beba2cbf41]',
      page: '15',
    },
    {
      title: 'Part 4: Enhance Learning with Bookshelf',
      cfi: '/6/30[;vnd.vst.idref=vst-4d80c0ec-c94b-4ade-956c-c7beba2cbf41]',
      page: '15',
    },
    {
      title: 'Navigate an eBook in Bookshelf Online',
      cfi: '/6/32[;vnd.vst.idref=vst-9982048e-f662-4957-9b3f-e3f3c5b4dcbd]',
      page: '16',
    },
    {
      title: 'Video Demonstration: Tools for Navigating an eBook',
      cfi: '/6/34[;vnd.vst.idref=vst-34b9bf9d-b2b6-4577-b870-fb3900db224d]',
      page: '17',
    },
    {
      title: 'Learning Check: Navigating an eBook',
      cfi: '/6/36[;vnd.vst.idref=vst-e246fd61-edbb-4d5a-a432-bef2f8e17d40]',
      page: '18',
    },
    {
      title: 'Search for Key Words',
      cfi: '/6/38[;vnd.vst.idref=vst-9e8556a2-dae1-41bf-99ed-0b9cfe69180b]',
      page: '19',
    },
    {
      title: 'Search for an Exact Phrase',
      cfi: '/6/40[;vnd.vst.idref=vst-e9babc51-7aad-4a10-9e08-3f8f95b5d34a]',
      page: '20',
    },
    {
      title: 'Search Across Your Library',
      cfi: '/6/42[;vnd.vst.idref=vst-996a8bd0-0743-4876-9c0b-243b098f34da]',
      page: '21',
    },
    {
      title: 'Learning Check: Searching for Content',
      cfi: '/6/44[;vnd.vst.idref=vst-8cfc6d45-cdd8-4145-a70d-eee280a5fedf]',
      page: '22',
    },
    {
      title: 'Highlight Text and Add Notes',
      cfi: '/6/46[;vnd.vst.idref=vst-830e2f21-8f48-48c9-be3e-ae7d27bfa68c]',
      page: '23',
    },
    {
      title: 'Video Demonstration: Making Highlights and Notes',
      cfi: '/6/48[;vnd.vst.idref=vst-f1fc6ed5-ca4c-4d01-a08d-518513964317]',
      page: '24',
    },
    {
      title: 'Manage Highlighters',
      cfi: '/6/50[;vnd.vst.idref=vst-48506c57-a291-414c-aa8e-7ed7cd8ed89d]',
      page: '25',
    },
    {
      title: 'Video Demonstration: Managing Highlighters',
      cfi: '/6/52[;vnd.vst.idref=vst-a6c7b7bf-7e6b-4aab-829f-ab61fbd7d367]',
      page: '26',
    },
    {
      title: 'Learning Check: Creating Highlights and Managing Highlighters',
      cfi: '/6/54[;vnd.vst.idref=vst-47f9ee6e-042a-46fc-8eee-daeb5f9b4fd8]',
      page: '27',
    },
    {
      title: 'Subscribe to Other Bookshelf Users',
      cfi: '/6/56[;vnd.vst.idref=vst-571fdb7c-2547-4bed-8bc6-59821e36092b]',
      page: '28',
    },
    {
      title: 'Share Highlights and Notes',
      cfi: '/6/58[;vnd.vst.idref=vst-eaf11d17-7b35-4189-82d9-299a35aeab78]',
      page: '29',
    },
    {
      title: 'Video Demonstration: Sharing and Subscribing',
      cfi: '/6/60[;vnd.vst.idref=vst-e46a628b-ab7c-42f9-8e7a-5aafd1503001]',
      page: '30',
    },
    {
      title: 'Manage Your Notebook',
      cfi: '/6/62[;vnd.vst.idref=vst-6d6266f0-4b68-4b7d-a0e0-1322c62e6389]',
      page: '31',
    },
    {
      title: 'Study with Review Mode',
      cfi: '/6/64[;vnd.vst.idref=vst-af780b01-1961-42a7-8aa5-8c0da20aaa04]',
      page: '32',
    },
    {
      title: 'Video Demonstration: Notebook and Review Mode',
      cfi: '/6/66[;vnd.vst.idref=vst-aca7b9db-ba85-4393-87a2-fb7ad6b4c3c4]',
      page: '33',
    },
    {
      title: 'Learning Check: Notebook and Review Mode',
      cfi: '/6/68[;vnd.vst.idref=vst-76d16952-eb1b-400e-92b6-7d18b656afa1]',
      page: '34',
    },
    {
      title: 'Study with Flash Cards',
      cfi: '/6/70[;vnd.vst.idref=vst-2b3481e1-596a-49ac-a50b-76ea73658c18]',
      page: '35',
    },
    {
      title: 'Video Demonstration: Creating Flashcards',
      cfi: '/6/72[;vnd.vst.idref=vst-b19a9bba-1155-4944-82ef-73d1e71891ea]',
      page: '36',
    },
    {
      title: 'Learn with Text-to-Speech',
      cfi: '/6/74[;vnd.vst.idref=vst-65cd738c-65d4-486e-9eee-726de86c85db]',
      page: '37',
    },
    {
      title: 'Part 5: Recap and Action Items',
      cfi: '/6/76[;vnd.vst.idref=vst-2ee70751-8a10-432a-8918-1c49810add84]',
      page: '38',
    },
    {
      title: 'Steps to Make Bookshelf a Part of Your Routine',
      cfi: '/6/76[;vnd.vst.idref=vst-2ee70751-8a10-432a-8918-1c49810add84]',
      page: '38',
    },
    {
      title: 'VitalSource Support Channels',
      cfi: '/6/78[;vnd.vst.idref=vst-b924e0ab-57dd-4aaa-b9d6-3012add8f2d8]',
      page: '39',
    },
  ],

  9781400847402: [
    {
      title: 'Cover Page',
      cfi: '/6/2[;vnd.vst.idref=cover]',
      page: 'i',
    },
    {
      title: 'Title Page',
      cfi: '/6/6[;vnd.vst.idref=title]',
      page: 'iii',
    },
    {
      title: 'Copyright Page',
      cfi: '/6/8[;vnd.vst.idref=copy]',
      page: 'iv',
    },
    {
      title: 'Dedication Page',
      cfi: '/6/10[;vnd.vst.idref=ded]',
      page: 'v',
    },
    {
      title: 'Contents',
      cfi: '/6/12[;vnd.vst.idref=toc]',
      page: 'vii',
    },
    {
      title: 'Forward',
      cfi: '/6/14[;vnd.vst.idref=forward]',
      page: 'ix',
    },
    {
      title: 'Preface',
      cfi: '/6/16[;vnd.vst.idref=preface]',
      page: 'xix',
    },
    {
      title: 'Chapter 1: Armageddon',
      cfi: '/6/20[;vnd.vst.idref=ch1]',
      page: '3',
    },
    {
      title: 'Chapter 2: Ex Libro Lapidum Historia Mundi',
      cfi: '/6/22[;vnd.vst.idref=ch2]',
      page: '19',
    },
    {
      title: 'Chapter 3: Gradualist versus Catastrophist',
      cfi: '/6/24[;vnd.vst.idref=ch3]',
      page: '43',
    },
    {
      title: 'Chapter 4: Iridium',
      cfi: '/6/26[;vnd.vst.idref=ch4]',
      page: '59',
    },
    {
      title: 'Chapter 5: The Search for the Impact Site',
      cfi: '/6/28[;vnd.vst.idref=ch5]',
      page: '82',
    },
    {
      title: 'Chapter 6: The Crater of Doom',
      cfi: '/6/30[;vnd.vst.idref=ch6]',
      page: '106',
    },
    {
      title: 'Chapter 7: The World after Chicxulub',
      cfi: '/6/32[;vnd.vst.idref=ch7]',
      page: '130',
    },
    {
      title: 'Notes',
      cfi: '/6/34[;vnd.vst.idref=ch8]',
      page: '147',
    },
    {
      title: 'Index',
      cfi: '/6/36[;vnd.vst.idref=ch9]',
      page: '171',
    },
  ],
};
