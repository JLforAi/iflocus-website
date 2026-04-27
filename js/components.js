// Shared header and footer components

const HEADER_HTML = `
<header class="site-header">
  <div class="nav-container">
    <a href="index.html" class="nav-logo">
      <img src="https://adlocus.com/wp-content/uploads/2023/07/Locus-logo.png" alt="iFLocus 絡客思行銷科技">
    </a>
    <nav>
      <ul class="nav-menu" id="navMenu">
        <li><a href="index.html">首頁</a></li>
        <li><a href="iflocus.html">iFLocus OMO</a></li>
        <li class="has-dropdown">
          <a href="branddrop.html">BrandDrop ▾</a>
          <ul class="dropdown-menu">
            <li><a href="branddrop.html">BrandDrop 介紹</a></li>
            <li><a href="branddrop-start.html">開始旅程</a></li>
          </ul>
        </li>
        <li><a href="locusad.html">場域手機推播廣告</a></li>
        <li><a href="ailocus.html">AiLocus</a></li>
        <li><a href="locus_ps.html">LocusPS 企業版</a></li>
        <li><a href="app_partners.html">加入APP聯播網</a></li>
        <li class="has-dropdown">
          <a href="case-studies.html">案例分享 ▾</a>
          <ul class="dropdown-menu">
            <li><a href="case-studies.html">全部案例</a></li>
            <li><a href="case-studies.html#election">智慧選戰</a></li>
            <li><a href="case-studies.html#3c">3C科技</a></li>
            <li><a href="case-studies.html#retail">優惠活動</a></li>
            <li><a href="case-studies.html#leisure">休閒生活</a></li>
            <li><a href="case-studies.html#fashion">女性時尚</a></li>
            <li><a href="case-studies.html#survey">名單問卷</a></li>
            <li><a href="case-studies.html#realestate">房地產</a></li>
            <li><a href="case-studies.html#event">實體活動</a></li>
            <li><a href="case-studies.html#omo">虛實整合</a></li>
            <li><a href="case-studies.html#member">會員推廣</a></li>
            <li><a href="case-studies.html#product">產品推廣</a></li>
            <li><a href="case-studies.html#telecom">電信通訊</a></li>
            <li><a href="case-studies.html#finance">金融保險</a></li>
            <li><a href="case-studies.html#food">食品餐飲</a></li>
            <li><a href="case-studies.html#hk">香港地區</a></li>
          </ul>
        </li>
        <li><a href="about_us.html">關於我們</a></li>
        <li><a href="news.html">最新消息</a></li>
        <li><a href="contact_us.html" class="nav-contact-btn">聯絡我們</a></li>
      </ul>
    </nav>
    <button class="nav-hamburger" id="navHamburger" aria-label="選單">
      <span></span><span></span><span></span>
    </button>
  </div>
</header>`;

const FOOTER_HTML = `
<footer class="site-footer">
  <div class="footer-inner">
    <div class="footer-brand">
      <img src="https://adlocus.com/wp-content/uploads/2023/07/Locus-logo.png" alt="iFLocus">
      <p>iFLocus 絡客思行銷科技，以「場域行銷科技」為核心，結合大數據與AI運算，提供企業精準的場域行動廣告與整合行銷解決方案。</p>
      <a href="mailto:sales@iflocus.com" class="footer-email">sales@iflocus.com</a>
    </div>
    <div class="footer-col">
      <h4>產品服務</h4>
      <ul>
        <li><a href="iflocus.html">iFLocus OMO</a></li>
        <li><a href="branddrop.html">BrandDrop</a></li>
        <li><a href="locusad.html">場域手機推播廣告</a></li>
        <li><a href="ailocus.html">AiLocus</a></li>
        <li><a href="locus_ps.html">LocusPS 企業版</a></li>
        <li><a href="app_partners.html">加入APP聯播網</a></li>
      </ul>
    </div>
    <div class="footer-col">
      <h4>資源</h4>
      <ul>
        <li><a href="case-studies.html">案例分享</a></li>
        <li><a href="news.html">最新消息</a></li>
        <li><a href="about_us.html">關於我們</a></li>
        <li><a href="contact_us.html">聯絡我們</a></li>
        <li><a href="privacy.html">隱私權政策</a></li>
      </ul>
    </div>
    <div class="footer-col">
      <h4>聯絡資訊</h4>
      <ul>
        <li><a href="mailto:sales@iflocus.com">sales@iflocus.com</a></li>
        <li style="color:rgba(255,255,255,0.5);font-size:13px;padding:6px 0">台北市中山區松江路87號11樓</li>
        <li><a href="https://www.facebook.com/LOCUS.iFLocus" target="_blank">Facebook</a></li>
        <li><a href="https://ps.adlocus.com/" target="_blank">操作平台</a></li>
      </ul>
    </div>
  </div>
  <div class="footer-bottom">
    <p>Copyright © 2026 iFLocus Marketing Technology CO., LTD. All rights reserved.</p>
  </div>
</footer>
<button class="back-to-top" id="backToTop" title="回到頂部">↑</button>`;

// Inject components
document.addEventListener('DOMContentLoaded', function () {
  // Favicon
  if (!document.querySelector('link[rel="icon"]')) {
    const favicon = document.createElement('link');
    favicon.rel = 'icon';
    favicon.type = 'image/png';
    favicon.href = '/images/favicon.png';
    document.head.appendChild(favicon);
  }
  // Insert header before first element
  document.body.insertAdjacentHTML('afterbegin', HEADER_HTML);
  // Insert footer at end
  document.body.insertAdjacentHTML('beforeend', FOOTER_HTML);
});
