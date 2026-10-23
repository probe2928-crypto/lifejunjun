const $ = id => document.getElementById(id);
const postList = $('boardList');
const form = $('boardForm');
const status = $('boardStatus');
let selectedCategory = '전체';
let cursor = null;
let posts = [];
let loading = false;
let requestVersion = 0;
let deletionKeys = {};
try { deletionKeys = JSON.parse(localStorage.getItem('unseenscene-delete-keys') || '{}'); } catch { /* No stored deletion keys. */ }
const dateFormat = new Intl.DateTimeFormat('ko-KR', { timeZone: 'Asia/Seoul', dateStyle: 'medium' });
// GitHub Pages 버전: 서버가 없어서 게시판·저널은 정적 JSON, 새 글은 편집실 메일로 보내 검토 후 게시
async function api(path, options) {
  const method = (options && options.method) || 'GET';
  if (path.startsWith('/api/journal')) return fetch('journal.json', { cache: 'no-store' }).then(r => r.json());
  if (path.startsWith('/api/community') && method === 'GET') {
    const data = await fetch('community.json', { cache: 'no-store' }).then(r => r.json());
    const q = new URLSearchParams(path.split('?')[1] || '');
    const cat = q.get('category');
    const list = (data.posts || []).filter(p => !cat || cat === '전체' || p.category === cat);
    return { posts: list, nextCursor: null };
  }
  if (path.startsWith('/api/community') && method === 'POST') {
    const b = JSON.parse(options.body);
    if (b.website) throw new Error('등록하지 못했습니다.');
    if (!b.author || !b.title || !b.body) throw new Error('닉네임, 제목, 내용을 채워주세요.');
    if (!b.publicConsent) throw new Error('공개 동의에 체크해주세요.');
    const r = await fetch('https://formsubmit.co/ajax/probe2928@gmail.com', { method: 'POST', headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
      body: JSON.stringify({ _subject: `[여백의 지도 커뮤니티 ${b.category}] ${b.title}`, _template: 'box', _captcha: 'false', 브랜드: '여백의 지도', 게시판: b.category, 닉네임: b.author, 제목: b.title, 내용: b.body }) });
    const j = await r.json().catch(() => ({}));
    if (!(j.success === true || j.success === 'true')) throw new Error('지금은 글을 보내지 못했어요. 잠시 후 다시 시도하거나 카카오톡 오픈채팅으로 남겨주세요.');
    return { pending: true, post: { id: 'pending-' + Date.now() } };
  }
  throw new Error('요청을 처리하지 못했습니다.');
}
function renderPosts() {
  postList.replaceChildren();
  if (!posts.length) {
    const empty = document.createElement('p');
    empty.className = 'notice'; empty.textContent = '아직 등록된 글이 없습니다. 첫 여행 이야기를 남겨주세요.';
    postList.append(empty);
  }
  for (const post of posts) {
    const item = document.createElement('article'); item.className = 'board-item';
    const meta = document.createElement('span'); meta.className = 'micro';
    meta.textContent = `${post.category} / ${post.author} / ${dateFormat.format(new Date(post.createdAt))}`;
    const title = document.createElement('h3'); title.textContent = post.title;
    const body = document.createElement('p'); body.textContent = post.body;
    const report = document.createElement('a'); report.className = 'muted-link'; report.textContent = '글 신고 · 운영 문의';
    report.href = `mailto:probe2928@gmail.com?subject=${encodeURIComponent('커뮤니티 글 신고: ' + post.id)}`;
    item.append(meta, title, body, report);
    if (deletionKeys[post.id]) {
      const remove = document.createElement('button'); remove.type = 'button'; remove.className = 'pill'; remove.textContent = '내 글 삭제';
      const result = document.createElement('p'); result.setAttribute('role', 'status');
      let confirmed = false;
      remove.onclick = async () => {
        if (!confirmed) { confirmed = true; remove.textContent = '영구 삭제 확인'; result.textContent = '이 글을 삭제하면 복원할 수 없습니다. 한 번 더 누르면 삭제됩니다.'; return; }
        remove.disabled = true;
        try {
          await api('/api/community', { method: 'DELETE', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ id: post.id, deleteToken: deletionKeys[post.id] }) });
          delete deletionKeys[post.id];
          try { localStorage.setItem('unseenscene-delete-keys', JSON.stringify(deletionKeys)); } catch { /* Memory key is removed. */ }
          posts = posts.filter(value => value.id !== post.id); renderPosts();
          $('boardLoadStatus').textContent = '글을 삭제했습니다.';
        } catch (error) { result.textContent = error.message; remove.disabled = false; }
      };
      item.append(remove, result);
    }
    postList.append(item);
  }
  $('boardMore').hidden = !cursor;
}
async function loadPosts(append = false) {
  const version = ++requestVersion;
  loading = true;
  $('boardLoadStatus').textContent = '여행 이야기를 불러오는 중입니다.';
  $('boardMore').disabled = true;
  try {
    const query = new URLSearchParams({ category: selectedCategory });
    if (append && cursor) query.set('before', cursor);
    const data = await api('/api/community?' + query);
    if (version !== requestVersion) return;
    posts = append ? [...posts, ...data.posts] : data.posts;
    cursor = data.nextCursor; renderPosts();
    $('boardLoadStatus').textContent = '';
  } catch (error) {
    if (version !== requestVersion) return;
    $('boardLoadStatus').textContent = error.message;
  } finally { if (version === requestVersion) { loading = false; $('boardMore').disabled = false; } }
}
document.querySelectorAll('#boardFilters button').forEach(button => button.onclick = () => {
  selectedCategory = button.dataset.category;
  document.querySelectorAll('#boardFilters button').forEach(value => value.classList.toggle('active', value === button));
  cursor = null; loadPosts();
});
$('boardMore').onclick = () => { if (!loading) loadPosts(true); };
$('boardRefresh').onclick = () => loadPosts();
form.onsubmit = async event => {
  event.preventDefault();
  const submit = form.querySelector('button[type="submit"]');
  submit.disabled = true; status.textContent = '등록 중입니다.';
  const value = id => $(id).value.trim();
  try {
    const data = await api('/api/community', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ category: value('boardCategory'), author: value('boardAuthor'), title: value('boardTitle'), body: value('boardBody'), website: value('boardWebsite'), publicConsent: $('boardPublicConsent').checked }) });
    form.reset(); status.textContent = '고마워요! 편집실이 확인한 뒤 게시판에 올릴게요.';
    selectedCategory = '전체';
    document.querySelectorAll('#boardFilters button').forEach(button => button.classList.toggle('active', button.dataset.category === '전체'));
    await loadPosts();
  } catch (error) { status.textContent = error.message; }
  finally { submit.disabled = false; }
};

function editorialFigure(key, cover = false) {
  const photo = window.travelPhotos[key];
  const figure = document.createElement('figure'); figure.className = cover ? 'journal-cover' : 'journal-photo';
  const anchor = document.createElement('a'); anchor.href = photo.src; anchor.target = '_blank'; anchor.rel = 'noopener'; anchor.setAttribute('aria-label', photo.caption + ' 사진 크게 보기');
  const image = document.createElement('img'); image.src = photo.src; image.alt = photo.caption; image.loading = 'lazy'; image.width = 1000; image.height = 700; anchor.append(image);
  const caption = document.createElement('figcaption'); caption.append(document.createTextNode(photo.caption + ' · '));
  const credit = document.createElement('a'); credit.href = photo.source; credit.textContent = photo.author + ' / Unsplash'; credit.target = '_blank'; credit.rel = 'noopener noreferrer'; caption.append(credit);
  figure.append(anchor, caption); return figure;
}
async function loadJournal() {
  try {
    const data = await api('/api/journal');
    const container = $('journalArticles'); container.replaceChildren();
    for (const article of data.articles) {
      const card = document.createElement('article'); card.className = 'editor-card'; card.id = 'journal-' + article.id;
      const meta = document.createElement('span'); meta.className = 'micro'; meta.textContent = article.category + ' / ' + dateFormat.format(new Date(article.publishAt));
      const title = document.createElement('h3'); title.textContent = article.title;
      const lead = document.createElement('p'); lead.className = 'standfirst'; lead.textContent = article.lead;
      const intro = document.createElement('p'); intro.textContent = article.paragraphs[0];
      const photoKeys = window.journalPhotoSets[article.id] || ['samarkand', 'tainan', 'oman'];
      const details = document.createElement('details'), summary = document.createElement('summary'); summary.textContent = '칼럼 계속 읽기'; details.append(summary);
      for (const [index, text] of article.paragraphs.slice(1).entries()) { const paragraph = document.createElement('p'); paragraph.textContent = text; details.append(paragraph); if (photoKeys[index + 1]) details.append(editorialFigure(photoKeys[index + 1])); }
      const imageNote=document.createElement('p'); imageNote.className='tiny-note'; imageNote.textContent='사진은 해당 여행지의 자료 사진이며, 에세이는 사진 속 장소를 실제 체험한 후기로 작성한 글이 아닙니다.'; details.append(imageNote);
      if (article.source) {
        const link = document.createElement('a'); link.className = 'muted-link'; link.textContent = '역사 사실 참고: ' + article.source.label + ' ↗';
        link.href = article.source.url; link.target = '_blank'; link.rel = 'noopener noreferrer'; details.append(link);
      }
      card.append(editorialFigure(photoKeys[0], true), meta, title, lead, intro, details); container.append(card);
    }
    $('journalSchedule').textContent = data.nextRelease ? '매주 월·수·금 오전 9시 · 다음 칼럼 ' + dateFormat.format(new Date(data.nextRelease)) + ' 공개' : '준비한 연재가 모두 공개되었습니다. 다음 편을 준비하고 있습니다.';
  } catch { $('journalSchedule').textContent = '칼럼 서버 연결을 기다리는 중입니다. 창간호를 먼저 읽어보세요.'; }
}
loadPosts(); loadJournal();
