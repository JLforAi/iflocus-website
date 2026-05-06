// Shared header and footer components

const HEADER_HTML = `
<header class="site-header">
  <div class="nav-container">
    <a href="index.html" class="nav-logo">
      <img src="images/logos/locus-color-word.png" alt="LOCUS 絡客思行銷科技">
    </a>
    <nav>
      <ul class="nav-menu" id="navMenu">
        <li><a href="index.html">首頁</a></li>
        <li class="has-dropdown">
          <a href="iflocus.html">iFLocus ▾</a>
          <ul class="dropdown-menu">
            <li><a href="brand-philosophy.html">品牌理念</a></li>
            <li><a href="iflocus.html">OMO應援服務</a></li>
            <li><a href="sports-marketing.html">運動行銷</a></li>
            <li><a href="integrated-marketing.html">整合行銷</a></li>
            <li><a href="corporate-training.html">企業培訓</a></li>
            <li><a href="video-production.html">影音拍攝</a></li>
          </ul>
        </li>
        <li class="has-dropdown">
          <a href="ailocus.html">AiLocus ▾</a>
          <ul class="dropdown-menu">
            <li><a href="ailocus.html">Ai大數據</a></li>
            <li><a href="locusad.html">場域手機推播廣告</a></li>
            <li><a href="locusad.html">企業版APP場域推播服務</a></li>
            <li><a href="app_partners.html">加入APP聯播網</a></li>
            <li><a href="case-studies.html">案例分享</a></li>
          </ul>
        </li>
        <li class="has-dropdown">
          <a href="branddrop.html">BrandDrop ▾</a>
          <ul class="dropdown-menu">
            <li><a href="branddrop.html">介紹</a></li>
            <li><a href="branddrop-start.html">開始旅程</a></li>
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
      <img src="images/logos/locus-color-word.png" alt="LOCUS 絡客思行銷科技">
      <p><strong>絡客思行銷科技</strong>旗下兩大主要服務：<strong>iFLocus</strong> 在地影響力營銷與 OMO 整合行銷，以及 <strong>AiLocus</strong> 位置大數據與 AI 智能洞察，協助品牌串連線上與線下，提升聲量、信任與實際轉換。</p>
      <a href="mailto:sales@iflocus.com" class="footer-email">sales@iflocus.com</a>
    </div>
    <div class="footer-col">
      <h4>產品服務</h4>
      <ul>
        <li><a href="iflocus.html">OMO應援服務</a></li>
        <li><a href="ailocus.html">Ai大數據</a></li>
        <li><a href="locusad.html">場域手機推播廣告</a></li>
        <li><a href="locusad.html">企業版APP場域推播服務</a></li>
        <li><a href="app_partners.html">加入APP聯播網</a></li>
        <li><a href="branddrop.html">BrandDrop</a></li>
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
    <p>Copyright © 2026 Locus Marketing Technology CO., LTD. All rights reserved.</p>
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
