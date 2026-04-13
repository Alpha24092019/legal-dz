// البحث
const searchToggle = document.querySelector('.search-toggle');
const searchModal = document.getElementById('searchModal');
const closeSearch = document.getElementById('closeSearch');
const searchInput = document.getElementById('searchInput');

searchToggle?.addEventListener('click', () => {
  searchModal.classList.add('active');
  searchInput.focus();
});

closeSearch?.addEventListener('click', () => {
  searchModal.classList.remove('active');
});

searchModal?.addEventListener('click', (e) => {
  if (e.target === searchModal) {
    searchModal.classList.remove('active');
  }
});

// القائمة المتنقلة
const mobileToggle = document.querySelector('.mobile-menu-toggle');
const navList = document.querySelector('.nav-list');

mobileToggle?.addEventListener('click', () => {
  navList.classList.toggle('active');
});

// البحث الفوري (سيتم ربطه لاحقاً مع Fuse.js أو Pagefind)
let searchIndex = [];

// تحميل فهرس البحث
async function loadSearchIndex() {
  try {
    const response = await fetch('/index.json');
    searchIndex = await response.json();
  } catch (e) {
    console.log('Search index not loaded yet');
  }
}

if (searchInput) {
  searchInput.addEventListener('input', (e) => {
    const query = e.target.value.toLowerCase();
    if (query.length < 2) return;
    
    const results = searchIndex.filter(item => 
      item.title.toLowerCase().includes(query) ||
      item.content.toLowerCase().includes(query)
    ).slice(0, 5);
    
    displayResults(results);
  });
}

function displayResults(results) {
  const container = document.getElementById('searchResults');
  if (!results.length) {
    container.innerHTML = '<p>لا توجد نتائج</p>';
    return;
  }
  
  container.innerHTML = results.map(item => `
    <a href="${item.permalink}" class="search-result">
      <h4>${item.title}</h4>
      <p>${item.summary}</p>
    </a>
  `).join('');
}

// تحميل الفهرس عند البدء
loadSearchIndex();