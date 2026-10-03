/**
 * Netflix AI Recommender - Frontend Controller
 * Handles live feed rendering, profile switching, real-time ratings,
 * algorithm weight tuning, and modal details.
 */

// Application State
const state = {
  userId: 'user_1',
  profiles: [],
  weights: { cf: 0.45, content: 0.40, pop: 0.15 },
  currentFeed: null,
  activeModalMovie: null,
  searchDebounceTimer: null
};

// DOM Elements
const el = {
  navbar: document.getElementById('navbar'),
  profileBtn: document.getElementById('profileBtn'),
  profileMenu: document.getElementById('profileMenu'),
  profileList: document.getElementById('profileList'),
  navAvatar: document.getElementById('navAvatar'),
  navUserName: document.getElementById('navUserName'),
  resetProfileBtn: document.getElementById('resetProfileBtn'),

  // Billboard
  billboardBackdrop: document.getElementById('billboardBackdrop'),
  billboardTitle: document.getElementById('billboardTitle'),
  billboardTagline: document.getElementById('billboardTagline'),
  billboardYear: document.getElementById('billboardYear'),
  billboardAge: document.getElementById('billboardAge'),
  billboardDuration: document.getElementById('billboardDuration'),
  billboardImdb: document.getElementById('billboardImdb'),
  billboardGenres: document.getElementById('billboardGenres'),
  billboardOverview: document.getElementById('billboardOverview'),
  billboardMatch: document.getElementById('billboardMatch'),
  billboardReason: document.getElementById('billboardReason'),
  billboardPlayBtn: document.getElementById('billboardPlayBtn'),
  billboardWatchlistBtn: document.getElementById('billboardWatchlistBtn'),
  billboardWatchlistText: document.getElementById('billboardWatchlistText'),
  billboardInfoBtn: document.getElementById('billboardInfoBtn'),

  // Rows & Container
  rowsContainer: document.getElementById('rowsContainer'),

  // Search
  searchContainer: document.getElementById('searchContainer'),
  searchToggleBtn: document.getElementById('searchToggleBtn'),
  searchInput: document.getElementById('searchInput'),
  clearSearchBtn: document.getElementById('clearSearchBtn'),
  searchOverlay: document.getElementById('searchOverlay'),
  searchGrid: document.getElementById('searchGrid'),
  searchQueryDisplay: document.getElementById('searchQueryDisplay'),
  closeSearchOverlay: document.getElementById('closeSearchOverlay'),

  // Modal
  movieModal: document.getElementById('movieModal'),
  modalCloseBtn: document.getElementById('modalCloseBtn'),
  modalBackdrop: document.getElementById('modalBackdrop'),
  modalTitle: document.getElementById('modalTitle'),
  modalMatch: document.getElementById('modalMatch'),
  modalBodyMatch: document.getElementById('modalBodyMatch'),
  modalDirectorTag: document.getElementById('modalDirectorTag'),
  modalYear: document.getElementById('modalYear'),
  modalAge: document.getElementById('modalAge'),
  modalDuration: document.getElementById('modalDuration'),
  modalOverview: document.getElementById('modalOverview'),
  modalTagline: document.getElementById('modalTagline'),
  modalDirector: document.getElementById('modalDirector'),
  modalCast: document.getElementById('modalCast'),
  modalGenresList: document.getElementById('modalGenresList'),
  modalKeywords: document.getElementById('modalKeywords'),
  modalPrimaryReason: document.getElementById('modalPrimaryReason'),
  modalUserName: document.getElementById('modalUserName'),
  modalBarCf: document.getElementById('modalBarCf'),
  modalValCf: document.getElementById('modalValCf'),
  modalBarContent: document.getElementById('modalBarContent'),
  modalValContent: document.getElementById('modalValContent'),
  modalBarPop: document.getElementById('modalBarPop'),
  modalValPop: document.getElementById('modalValPop'),
  modalMoreGrid: document.getElementById('modalMoreGrid'),
  modalWatchlistBtn: document.getElementById('modalWatchlistBtn'),
  modalUserRatingText: document.getElementById('modalUserRatingText'),
  modalPlayBtn: document.getElementById('modalPlayBtn'),

  // Drawer
  algoDrawer: document.getElementById('algoDrawer'),
  drawerBackdrop: document.getElementById('drawerBackdrop'),
  openAlgoDrawerBtn: document.getElementById('openAlgoDrawerBtn'),
  closeAlgoDrawerBtn: document.getElementById('closeAlgoDrawerBtn'),
  sliderCf: document.getElementById('sliderCf'),
  sliderContent: document.getElementById('sliderContent'),
  sliderPop: document.getElementById('sliderPop'),
  valCf: document.getElementById('valCf'),
  valContent: document.getElementById('valContent'),
  valPop: document.getElementById('valPop'),
  applyWeightsBtn: document.getElementById('applyWeightsBtn'),
  resetWeightsBtn: document.getElementById('resetWeightsBtn'),

  // Toast
  toastContainer: document.getElementById('toastContainer'),

  // Theater Player Modal
  theaterModal: document.getElementById('theaterModal'),
  theaterIframe: document.getElementById('theaterIframe'),
  theaterHtmlVideo: document.getElementById('theaterHtmlVideo'),
  theaterBadgeTag: document.getElementById('theaterBadgeTag'),
  theaterTitle: document.getElementById('theaterTitle'),
  theaterMatch: document.getElementById('theaterMatch'),
  theaterOverview: document.getElementById('theaterOverview'),
  theaterDirector: document.getElementById('theaterDirector'),
  theaterCast: document.getElementById('theaterCast'),
  theaterCloseBtn: document.getElementById('theaterCloseBtn'),
  theaterBackBtn: document.getElementById('theaterBackBtn'),
  theaterWatchlistBtn: document.getElementById('theaterWatchlistBtn'),
  theaterWatchlistText: document.getElementById('theaterWatchlistText'),
  theaterNextRecBtn: document.getElementById('theaterNextRecBtn'),

  // Modal Providers
  modalWatchProvidersGroup: document.getElementById('modalWatchProvidersGroup'),
  modalProviderButtons: document.getElementById('modalProviderButtons')
};

// ============================================================
// INITIALIZATION
// ============================================================
async function init() {
  setupEventListeners();
  await loadProfiles();
  await loadFeed();
}

function setupEventListeners() {
  // Navbar scroll background
  window.addEventListener('scroll', () => {
    if (window.scrollY > 40) {
      el.navbar.classList.add('scrolled');
    } else {
      el.navbar.classList.remove('scrolled');
    }
  });

  // Profile Menu Toggle
  el.profileBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    el.profileMenu.classList.toggle('show');
  });

  document.addEventListener('click', () => {
    el.profileMenu.classList.remove('show');
  });

  // Reset Profile
  el.resetProfileBtn.addEventListener('click', async () => {
    try {
      await fetch(`/api/reset-profile?user_id=${state.userId}`, { method: 'POST' });
      showToast('Profile reset to default taste profile');
      await loadFeed();
    } catch (err) {
      console.error(err);
    }
  });

  // Algorithm Drawer Toggle
  el.openAlgoDrawerBtn.addEventListener('click', () => {
    el.algoDrawer.classList.add('open');
    el.drawerBackdrop.classList.add('show');
  });

  el.closeAlgoDrawerBtn.addEventListener('click', closeAlgoDrawer);
  el.drawerBackdrop.addEventListener('click', closeAlgoDrawer);

  // Sliders input
  el.sliderCf.addEventListener('input', (e) => el.valCf.textContent = `${e.target.value}%`);
  el.sliderContent.addEventListener('input', (e) => el.valContent.textContent = `${e.target.value}%`);
  el.sliderPop.addEventListener('input', (e) => el.valPop.textContent = `${e.target.value}%`);

  el.applyWeightsBtn.addEventListener('click', async () => {
    const cf = parseFloat(el.sliderCf.value) / 100;
    const content = parseFloat(el.sliderContent.value) / 100;
    const pop = parseFloat(el.sliderPop.value) / 100;
    state.weights = { cf, content, pop };
    closeAlgoDrawer();
    showToast(`Applied weights: CF ${el.sliderCf.value}%, Content ${el.sliderContent.value}%, Pop ${el.sliderPop.value}%`);
    await loadFeed();
  });

  el.resetWeightsBtn.addEventListener('click', async () => {
    el.sliderCf.value = 45; el.valCf.textContent = '45%';
    el.sliderContent.value = 40; el.valContent.textContent = '40%';
    el.sliderPop.value = 15; el.valPop.textContent = '15%';
    state.weights = { cf: 0.45, content: 0.40, pop: 0.15 };
    closeAlgoDrawer();
    showToast('Reset to Netflix standard recommendation weights');
    await loadFeed();
  });

  // Modal Close
  el.modalCloseBtn.addEventListener('click', closeModal);
  el.movieModal.addEventListener('click', (e) => {
    if (e.target === el.movieModal) closeModal();
  });

  // Modal Stars Rating
  const starElements = document.querySelectorAll('.rating-stars-group .star');
  starElements.forEach(star => {
    star.addEventListener('mouseenter', () => {
      const val = parseInt(star.dataset.rating);
      highlightStars(val);
    });
    star.addEventListener('mouseleave', () => {
      const activeRating = state.activeModalMovie ? (state.activeModalMovie.user_rating || 0) : 0;
      highlightStars(activeRating);
    });
    star.addEventListener('click', async () => {
      const val = parseInt(star.dataset.rating);
      if (state.activeModalMovie) {
        await rateMovie(state.activeModalMovie.id, val);
      }
    });
  });

  // Watchlist buttons
  el.modalWatchlistBtn.addEventListener('click', async () => {
    if (state.activeModalMovie) {
      await toggleWatchlist(state.activeModalMovie.id);
    }
  });

  el.billboardWatchlistBtn.addEventListener('click', async () => {
    if (state.currentFeed && state.currentFeed.hero_movie) {
      await toggleWatchlist(state.currentFeed.hero_movie.id);
    }
  });

  el.billboardPlayBtn.addEventListener('click', () => {
    if (state.currentFeed && state.currentFeed.hero_movie) {
      playTrailer(state.currentFeed.hero_movie);
    }
  });

  el.billboardInfoBtn.addEventListener('click', () => {
    if (state.currentFeed && state.currentFeed.hero_movie) {
      openModal(state.currentFeed.hero_movie.id);
    }
  });

  el.modalPlayBtn.addEventListener('click', () => {
    if (state.activeModalMovie) {
      playTrailer(state.activeModalMovie);
    }
  });

  // Search Toggle
  el.searchToggleBtn.addEventListener('click', () => {
    el.searchContainer.classList.add('active');
    el.searchInput.focus();
  });

  el.searchInput.addEventListener('input', (e) => {
    const q = e.target.value.trim();
    if (q.length > 0) {
      el.clearSearchBtn.style.display = 'block';
    } else {
      el.clearSearchBtn.style.display = 'none';
      closeSearch();
      return;
    }
    clearTimeout(state.searchDebounceTimer);
    state.searchDebounceTimer = setTimeout(() => handleSearch(q), 250);
  });

  el.clearSearchBtn.addEventListener('click', () => {
    el.searchInput.value = '';
    el.clearSearchBtn.style.display = 'none';
    closeSearch();
  });

  el.closeSearchOverlay.addEventListener('click', closeSearch);

  // Theater modal events
  el.theaterCloseBtn.addEventListener('click', closeTheater);
  el.theaterBackBtn.addEventListener('click', closeTheater);
  el.theaterModal.addEventListener('click', (e) => {
    if (e.target === el.theaterModal) closeTheater();
  });
  el.theaterWatchlistBtn.addEventListener('click', async () => {
    if (state.activeTheaterMovie) {
      await toggleWatchlist(state.activeTheaterMovie.id);
      const isNowInWatchlist = !state.activeTheaterMovie.in_watchlist;
      state.activeTheaterMovie.in_watchlist = isNowInWatchlist;
      updateTheaterWatchlistState(isNowInWatchlist);
    }
  });
  el.theaterNextRecBtn.addEventListener('click', playNextRecommendation);

  // Keyboard shortcut: Escape closes theater, modal or drawer
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      if (el.theaterModal.style.display !== 'none') closeTheater();
      else if (el.movieModal.style.display !== 'none') closeModal();
      else if (el.algoDrawer.classList.contains('open')) closeAlgoDrawer();
    }
  });
}

function closeAlgoDrawer() {
  el.algoDrawer.classList.remove('open');
  el.drawerBackdrop.classList.remove('show');
}

function closeSearch() {
  el.searchOverlay.style.display = 'none';
  el.searchContainer.classList.remove('active');
}

// ============================================================
// PROFILE MANAGEMENT
// ============================================================
async function loadProfiles() {
  try {
    const res = await fetch('/api/profiles');
    const data = await res.json();
    state.profiles = data.profiles;
    renderProfileMenu();
    updateNavProfile();
  } catch (err) {
    console.error('Failed to load profiles:', err);
  }
}

function renderProfileMenu() {
  el.profileList.innerHTML = '';
  state.profiles.forEach(p => {
    const item = document.createElement('div');
    item.className = `profile-item ${p.id === state.userId ? 'active' : ''}`;
    item.innerHTML = `
      <img src="${p.avatar}" alt="${p.name}" class="avatar-img">
      <div class="profile-item-info">
        <span class="profile-item-name">${p.name}</span>
        <span class="profile-item-tag">${p.tagline}</span>
      </div>
    `;
    item.addEventListener('click', async () => {
      state.userId = p.id;
      updateNavProfile();
      renderProfileMenu();
      showToast(`Switched profile to ${p.name}`);
      await loadFeed();
    });
    el.profileList.appendChild(item);
  });
}

function updateNavProfile() {
  const current = state.profiles.find(p => p.id === state.userId);
  if (current) {
    el.navAvatar.src = current.avatar;
    el.navUserName.textContent = current.name;
  }
}

// ============================================================
// FEED & ROW RENDERING
// ============================================================
async function loadFeed() {
  try {
    const { cf, content, pop } = state.weights;
    const res = await fetch(`/api/feed?user_id=${state.userId}&cf=${cf}&content=${content}&pop=${pop}`);
    const feed = await res.json();
    state.currentFeed = feed;

    renderBillboard(feed.hero_movie);
    renderRows(feed.rows);
  } catch (err) {
    console.error('Failed to load feed:', err);
  }
}

function renderBillboard(movie) {
  if (!movie) return;

  el.billboardBackdrop.style.backgroundImage = `url('${movie.backdrop_url || movie.poster_url}')`;
  el.billboardTitle.textContent = movie.title;
  el.billboardTagline.textContent = movie.tagline || '';
  el.billboardYear.textContent = movie.year;
  el.billboardAge.textContent = movie.age_rating || 'PG-13';
  el.billboardDuration.textContent = movie.duration;
  el.billboardImdb.textContent = `★ ${movie.rating}`;
  el.billboardGenres.textContent = (movie.genres || []).join(' • ');
  el.billboardOverview.textContent = movie.overview;
  el.billboardMatch.textContent = `${movie.match_percentage || 95}% Match`;

  if (movie.explanation && movie.explanation.badges && movie.explanation.badges.length > 0) {
    el.billboardReason.textContent = movie.explanation.badges[0];
  } else {
    el.billboardReason.textContent = 'Top Pick';
  }

  // Watchlist state
  updateBillboardWatchlistState(movie.in_watchlist);
}

function updateBillboardWatchlistState(inWatchlist) {
  if (inWatchlist) {
    el.billboardWatchlistText.textContent = 'In My List';
    el.billboardWatchlistBtn.classList.add('btn-primary');
    el.billboardWatchlistBtn.classList.remove('btn-secondary');
  } else {
    el.billboardWatchlistText.textContent = 'My List';
    el.billboardWatchlistBtn.classList.remove('btn-primary');
    el.billboardWatchlistBtn.classList.add('btn-secondary');
  }
}

function renderRows(rows) {
  el.rowsContainer.innerHTML = '';

  rows.forEach(row => {
    if (!row.movies || row.movies.length === 0) return;

    const rowElem = document.createElement('div');
    rowElem.className = 'movie-row';
    rowElem.id = row.id;

    // Header
    const headerElem = document.createElement('div');
    headerElem.className = 'row-header';
    headerElem.innerHTML = `
      <div class="row-title-group">
        <h2 class="row-title">${row.title}</h2>
        <span class="row-subtitle">${row.subtitle || ''}</span>
      </div>
    `;

    // Slider wrapper
    const wrapper = document.createElement('div');
    wrapper.className = 'row-slider-wrapper';

    // Left & Right scroll arrows
    const leftArrow = document.createElement('button');
    leftArrow.className = 'slider-arrow left';
    leftArrow.innerHTML = `
      <svg viewBox="0 0 24 24" width="24" height="24" fill="currentColor">
        <path d="M15.41 7.41L14 6l-6 6 6 6 1.41-1.41L10.83 12z"/>
      </svg>
    `;

    const rightArrow = document.createElement('button');
    rightArrow.className = 'slider-arrow right';
    rightArrow.innerHTML = `
      <svg viewBox="0 0 24 24" width="24" height="24" fill="currentColor">
        <path d="M10 6L8.59 7.41 13.17 12l-4.58 4.59L10 18l6-6z"/>
      </svg>
    `;

    // Cards Container
    const cardsContainer = document.createElement('div');
    cardsContainer.className = 'row-cards';

    row.movies.forEach(movie => {
      const card = createMovieCard(movie);
      cardsContainer.appendChild(card);
    });

    leftArrow.addEventListener('click', () => {
      cardsContainer.scrollBy({ left: -600, behavior: 'smooth' });
    });

    rightArrow.addEventListener('click', () => {
      cardsContainer.scrollBy({ left: 600, behavior: 'smooth' });
    });

    wrapper.appendChild(leftArrow);
    wrapper.appendChild(cardsContainer);
    wrapper.appendChild(rightArrow);

    rowElem.appendChild(headerElem);
    rowElem.appendChild(wrapper);
    el.rowsContainer.appendChild(rowElem);
  });
}

function createMovieCard(movie) {
  const card = document.createElement('div');
  card.className = 'movie-card';

  const matchPct = movie.match_percentage || 85;
  const isFullMovie = movie.is_full_movie;
  const fullBadgeHtml = isFullMovie ? '<span class="card-full-badge">Full Movie</span>' : '';
  const reasonText = (movie.explanation && movie.explanation.primary_reason)
    ? movie.explanation.primary_reason
    : (movie.genres || []).slice(0, 2).join(' • ');

  card.innerHTML = `
    <span class="card-top-badge">${matchPct}% Match</span>
    ${fullBadgeHtml}
    <img src="${movie.poster_url}" alt="${movie.title}" class="card-poster" loading="lazy">
    <div class="card-overlay">
      <div class="card-quick-actions">
        <button class="circle-action-btn play-btn" title="${isFullMovie ? 'Play Complete Movie' : 'Play Preview'}" data-action="play">
          <svg viewBox="0 0 24 24" width="14" height="14" fill="currentColor">
            <path d="M8 5v14l11-7z"/>
          </svg>
        </button>
        <button class="circle-action-btn ${movie.in_watchlist ? 'active' : ''}" title="My List" data-action="watchlist">
          <svg viewBox="0 0 24 24" width="14" height="14" fill="currentColor">
            ${movie.in_watchlist
              ? '<path d="M9 16.2L4.8 12l-1.4 1.4L9 19 21 7l-1.4-1.4L9 16.2z"/>'
              : '<path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z"/>'}
          </svg>
        </button>
        <button class="circle-action-btn ${movie.user_rating ? 'active' : ''}" title="Rate 5 Stars" data-action="quick-rate">
          <svg viewBox="0 0 24 24" width="14" height="14" fill="currentColor">
            <path d="M12 17.27L18.18 21l-1.64-7.03L22 9.24l-7.19-.61L12 2 9.19 8.63 2 9.24l5.46 4.73L5.82 21z"/>
          </svg>
        </button>
        <button class="circle-action-btn" title="More Info" data-action="info" style="margin-left: auto;">
          <svg viewBox="0 0 24 24" width="14" height="14" fill="currentColor">
            <path d="M11 7h2v2h-2zm0 4h2v6h-2zm1-9C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8z"/>
          </svg>
        </button>
      </div>
      <div class="card-title">${movie.title}</div>
      <div class="card-meta-line">
        <span class="match-pct">${matchPct}% Match</span>
        <span>${movie.year}</span>
        <span>${movie.duration}</span>
      </div>
      <div class="card-genres">${(movie.genres || []).join(' • ')}</div>
      <div class="card-why-tag" title="${reasonText}">💡 ${reasonText}</div>
    </div>
  `;

  // Click card opens modal, unless an action button was clicked
  card.addEventListener('click', (e) => {
    const actionBtn = e.target.closest('button[data-action]');
    if (actionBtn) {
      e.stopPropagation();
      const action = actionBtn.dataset.action;
      if (action === 'play') playTrailer(movie);
      else if (action === 'watchlist') toggleWatchlist(movie.id);
      else if (action === 'quick-rate') rateMovie(movie.id, 5.0);
      else if (action === 'info') openModal(movie.id);
    } else {
      openModal(movie.id);
    }
  });

  return card;
}

// ============================================================
// MOVIE DETAIL MODAL & EXPLAINABILITY
// ============================================================
async function openModal(movieId) {
  try {
    const res = await fetch(`/api/movies/${movieId}?user_id=${state.userId}`);
    const data = await res.json();
    const movie = data.movie;
    state.activeModalMovie = { ...movie, ...data.user_context };

    // Fill modal fields
    el.modalBackdrop.src = movie.backdrop_url || movie.poster_url;
    el.modalTitle.textContent = movie.title;
    el.modalDirectorTag.textContent = `Directed by ${movie.director}`;
    el.modalYear.textContent = movie.year;
    el.modalAge.textContent = movie.age_rating || 'PG-13';
    el.modalDuration.textContent = movie.duration;
    el.modalOverview.textContent = movie.overview;
    el.modalTagline.textContent = movie.tagline ? `"${movie.tagline}"` : '';
    el.modalDirector.textContent = movie.director;
    el.modalCast.textContent = (movie.cast || []).join(', ');
    el.modalGenresList.textContent = (movie.genres || []).join(', ');

    // Keywords
    el.modalKeywords.innerHTML = '';
    (movie.keywords || []).forEach(kw => {
      const pill = document.createElement('span');
      pill.className = 'kw-pill';
      pill.textContent = `#${kw}`;
      el.modalKeywords.appendChild(pill);
    });

    // Match %
    const userProfile = state.profiles.find(p => p.id === state.userId);
    el.modalUserName.textContent = userProfile ? userProfile.name : 'You';

    // Metrics & Explainability from feed if available
    let feedMovie = null;
    if (state.currentFeed) {
      for (const r of state.currentFeed.rows) {
        const found = r.movies.find(m => m.id === movieId);
        if (found) { feedMovie = found; break; }
      }
    }

    const matchScore = feedMovie ? feedMovie.match_percentage : 92;
    el.modalMatch.textContent = `${matchScore}% Match`;
    el.modalBodyMatch.textContent = `${matchScore}% Match`;

    const metrics = (feedMovie && feedMovie.explanation && feedMovie.explanation.metrics) || {
      collaborative_affinity: 84.5,
      content_similarity: 88.0,
      popularity_factor: 94.2
    };

    el.modalValCf.textContent = `${metrics.collaborative_affinity}%`;
    el.modalBarCf.style.width = `${metrics.collaborative_affinity}%`;

    el.modalValContent.textContent = `${metrics.content_similarity}%`;
    el.modalBarContent.style.width = `${metrics.content_similarity}%`;

    el.modalValPop.textContent = `${metrics.popularity_factor}%`;
    el.modalBarPop.style.width = `${metrics.popularity_factor}%`;

    el.modalPrimaryReason.textContent = (feedMovie && feedMovie.explanation)
      ? feedMovie.explanation.primary_reason
      : `High thematic affinity to your favorite ${movie.genres[0]} titles.`;

    // Watchlist & Rating state
    updateModalWatchlistIcon(data.user_context.in_watchlist);
    const existingRating = data.user_context.rating;
    highlightStars(existingRating || 0);
    if (existingRating) {
      el.modalUserRatingText.textContent = `You rated: ${existingRating}★`;
      el.modalUserRatingText.style.color = 'var(--accent-gold)';
    } else {
      el.modalUserRatingText.textContent = 'Rate this title';
      el.modalUserRatingText.style.color = 'var(--text-muted)';
    }

    // Render Watch Providers & Full Movie button
    if (el.modalProviderButtons) {
      el.modalProviderButtons.innerHTML = '';
      if (movie.is_full_movie) {
        const fullBtn = document.createElement('button');
        fullBtn.className = 'btn btn-primary';
        fullBtn.style.padding = '6px 14px';
        fullBtn.style.fontSize = '12px';
        fullBtn.innerHTML = `▶ Stream Full Movie Free In-App`;
        fullBtn.addEventListener('click', () => {
          closeModal();
          playTrailer(movie);
        });
        el.modalProviderButtons.appendChild(fullBtn);
      } else if (movie.watch_providers && movie.watch_providers.length > 0) {
        movie.watch_providers.forEach(wp => {
          const a = document.createElement('a');
          a.className = 'provider-btn';
          a.href = wp.url;
          a.target = '_blank';
          a.rel = 'noopener noreferrer';
          a.innerHTML = `<span>${wp.icon}</span> <span>${wp.name}</span>`;
          el.modalProviderButtons.appendChild(a);
        });
      }
    }

    // Render "More Like This"
    renderMoreLikeThis(data.more_like_this || []);

    // Show modal
    el.movieModal.style.display = 'flex';
    document.body.style.overflow = 'hidden';
  } catch (err) {
    console.error('Failed to open modal:', err);
  }
}

function closeModal() {
  el.movieModal.style.display = 'none';
  document.body.style.overflow = 'auto';
  state.activeModalMovie = null;
}

function highlightStars(count) {
  const stars = document.querySelectorAll('.rating-stars-group .star');
  stars.forEach(s => {
    const r = parseInt(s.dataset.rating);
    if (r <= count) {
      s.classList.add('active');
    } else {
      s.classList.remove('active');
    }
  });
}

function updateModalWatchlistIcon(inWatchlist) {
  if (inWatchlist) {
    el.modalWatchlistBtn.classList.add('active');
    el.modalWatchlistBtn.innerHTML = `
      <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
        <path d="M9 16.2L4.8 12l-1.4 1.4L9 19 21 7l-1.4-1.4L9 16.2z"/>
      </svg>
    `;
  } else {
    el.modalWatchlistBtn.classList.remove('active');
    el.modalWatchlistBtn.innerHTML = `
      <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
        <path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z"/>
      </svg>
    `;
  }
}

function renderMoreLikeThis(movies) {
  el.modalMoreGrid.innerHTML = '';
  movies.forEach(m => {
    const card = document.createElement('div');
    card.className = 'more-card';
    card.innerHTML = `
      <img src="${m.backdrop_url || m.poster_url}" alt="${m.title}" class="more-card-img" loading="lazy">
      <div class="more-card-body">
        <div class="more-card-title">${m.title}</div>
        <div class="more-card-meta">
          <span class="match">${m.similarity_score}% Similar</span>
          <span>${m.year}</span>
        </div>
        <div class="more-card-desc">${m.overview}</div>
      </div>
    `;
    card.addEventListener('click', () => openModal(m.id));
    el.modalMoreGrid.appendChild(card);
  });
}

// ============================================================
// ACTIONS: RATE & WATCHLIST
// ============================================================
async function rateMovie(movieId, rating) {
  try {
    const res = await fetch('/api/rate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        user_id: state.userId,
        movie_id: movieId,
        rating: rating
      })
    });
    const data = await res.json();
    if (data.status === 'success') {
      showToast(`⭐ Rated ${rating}★! Updating your recommendation feed...`);
      highlightStars(rating);
      el.modalUserRatingText.textContent = `You rated: ${rating}★`;
      el.modalUserRatingText.style.color = 'var(--accent-gold)';

      if (state.activeModalMovie && state.activeModalMovie.id === movieId) {
        state.activeModalMovie.user_rating = rating;
      }
      // Re-fetch personalized feed in background
      await loadFeed();
    }
  } catch (err) {
    console.error('Failed to rate movie:', err);
  }
}

async function toggleWatchlist(movieId) {
  try {
    const res = await fetch('/api/watchlist', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        user_id: state.userId,
        movie_id: movieId
      })
    });
    const data = await res.json();
    if (data.status === 'success') {
      const inList = data.in_watchlist;
      showToast(inList ? 'Added to My List' : 'Removed from My List');
      if (state.activeModalMovie && state.activeModalMovie.id === movieId) {
        updateModalWatchlistIcon(inList);
      }
      if (state.currentFeed && state.currentFeed.hero_movie && state.currentFeed.hero_movie.id === movieId) {
        updateBillboardWatchlistState(inList);
      }
      await loadFeed();
    }
  } catch (err) {
    console.error('Failed to toggle watchlist:', err);
  }
}

function playTrailer(movie) {
  if (!movie) return;
  state.activeTheaterMovie = movie;

  // Close details modal if open
  if (el.movieModal.style.display !== 'none') {
    closeModal();
  }

  const isFull = movie.is_full_movie;
  const isMp4 = movie.stream_type === 'mp4' || (movie.stream_url && movie.stream_url.includes('.mp4'));

  if (isMp4) {
    // Native HTML5 Video Player with full seek, scrub, volume and fullscreen controls
    el.theaterIframe.style.display = 'none';
    el.theaterIframe.src = '';

    el.theaterHtmlVideo.style.display = 'block';
    el.theaterHtmlVideo.src = movie.stream_url;
    el.theaterHtmlVideo.currentTime = 0;
    el.theaterHtmlVideo.play().catch(e => console.log('Autoplay policy prevented audio play:', e));

    if (el.theaterBadgeTag) {
      el.theaterBadgeTag.textContent = 'COMPLETE FULL MOVIE (1080p)';
      el.theaterBadgeTag.classList.add('full-movie');
    }
    showToast(`▶ Streaming Complete Full Feature: "${movie.title}"`);
  } else {
    // YouTube Player (full movie or trailer)
    if (el.theaterHtmlVideo) {
      el.theaterHtmlVideo.pause();
      el.theaterHtmlVideo.style.display = 'none';
      el.theaterHtmlVideo.src = '';
    }

    el.theaterIframe.style.display = 'block';
    const trailerId = movie.trailer_youtube_id || 'zSWdZVtXT7E';
    const streamUrl = movie.stream_url || movie.trailer_url || `https://www.youtube.com/embed/${trailerId}?autoplay=1&rel=0&modestbranding=1&enablejsapi=1`;
    el.theaterIframe.src = streamUrl;

    if (el.theaterBadgeTag) {
      if (isFull) {
        el.theaterBadgeTag.textContent = 'COMPLETE FULL MOVIE';
        el.theaterBadgeTag.classList.add('full-movie');
        showToast(`▶ Streaming Complete Full Movie: "${movie.title}"`);
      } else {
        el.theaterBadgeTag.textContent = 'OFFICIAL HD TRAILER';
        el.theaterBadgeTag.classList.remove('full-movie');
        showToast(`▶ Streaming Preview: "${movie.title}"`);
      }
    }
  }

  el.theaterTitle.textContent = movie.title;
  el.theaterMatch.textContent = `${movie.match_percentage || 96}% Match`;
  el.theaterOverview.textContent = movie.overview;
  el.theaterDirector.textContent = `Director: ${movie.director}`;
  el.theaterCast.textContent = `Cast: ${(movie.cast || []).slice(0, 3).join(', ')}`;

  updateTheaterWatchlistState(movie.in_watchlist);

  el.theaterModal.style.display = 'flex';
  document.body.style.overflow = 'hidden';
}

function closeTheater() {
  if (el.theaterHtmlVideo) {
    el.theaterHtmlVideo.pause();
    el.theaterHtmlVideo.src = '';
    el.theaterHtmlVideo.style.display = 'none';
  }
  if (el.theaterIframe) {
    el.theaterIframe.src = '';
    el.theaterIframe.style.display = 'none';
  }
  el.theaterModal.style.display = 'none';
  document.body.style.overflow = 'auto';
  state.activeTheaterMovie = null;
}

function updateTheaterWatchlistState(inWatchlist) {
  if (inWatchlist) {
    el.theaterWatchlistText.textContent = 'In My List';
    el.theaterWatchlistBtn.classList.add('btn-primary');
    el.theaterWatchlistBtn.classList.remove('btn-secondary');
  } else {
    el.theaterWatchlistText.textContent = 'My List';
    el.theaterWatchlistBtn.classList.remove('btn-primary');
    el.theaterWatchlistBtn.classList.add('btn-secondary');
  }
}

function playNextRecommendation() {
  if (!state.currentFeed || !state.currentFeed.rows || state.currentFeed.rows.length === 0) return;
  const topPicks = state.currentFeed.rows[0].movies;
  if (!topPicks || topPicks.length === 0) return;

  const currentId = state.activeTheaterMovie ? state.activeTheaterMovie.id : null;
  let nextMovie = topPicks.find(m => m.id !== currentId);
  if (!nextMovie) nextMovie = topPicks[0];

  playTrailer(nextMovie);
}

// ============================================================
// SEARCH
// ============================================================
async function handleSearch(query) {
  if (!query) return;
  try {
    const res = await fetch(`/api/movies?q=${encodeURIComponent(query)}`);
    const data = await res.json();

    el.searchQueryDisplay.textContent = query;
    el.searchGrid.innerHTML = '';

    if (data.movies.length === 0) {
      el.searchGrid.innerHTML = `<div style="grid-column: 1/-1; color: #888; font-size: 16px; padding: 40px 0;">No movies found matching "${query}". Try searching for Nolan, Sci-Fi, DiCaprio, etc.</div>`;
    } else {
      data.movies.forEach(movie => {
        const card = createMovieCard(movie);
        el.searchGrid.appendChild(card);
      });
    }

    el.searchOverlay.style.display = 'block';
  } catch (err) {
    console.error('Search failed:', err);
  }
}

// ============================================================
// TOAST NOTIFICATIONS
// ============================================================
function showToast(message) {
  const toast = document.createElement('div');
  toast.className = 'toast';
  toast.innerHTML = `
    <svg viewBox="0 0 24 24" width="16" height="16" fill="#e50914">
      <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
    </svg>
    <span>${message}</span>
  `;
  el.toastContainer.appendChild(toast);

  setTimeout(() => {
    toast.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(10px)';
    setTimeout(() => toast.remove(), 400);
  }, 3200);
}

// Boot application
document.addEventListener('DOMContentLoaded', init);
