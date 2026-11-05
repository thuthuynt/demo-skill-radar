// Quay video demo trang hướng nghiệp trên khung điện thoại, có chấm chạm giả lập ngón tay.
// Cần server local đang chạy (cổng 8090). Chạy: npm run demo-video  →  demo-video/demo-huong-nghiep.webm
// HEADED=1 npm run demo-video: mở cửa sổ Chromium thật để quay màn hình (Cmd+Shift+5) cho nét
import { chromium, devices } from 'playwright';
import { readFileSync, mkdirSync, rmSync } from 'node:fs';
import { spawnSync } from 'node:child_process';

const BASE = process.env.BASE || 'http://localhost:8090';
const OUT = new URL('../demo-video/', import.meta.url).pathname;
const copy = JSON.parse(readFileSync(new URL('../web/copy.hn.vi.json', import.meta.url), 'utf8'));
// hồ sơ mẫu: thích việc phân tích (I) và quy củ (C), vừa phải với kinh doanh (E) và giúp người (S)
const LIKE = { I: 2, C: 2, E: 1, S: 1, R: 0, A: 0 };
// CV mẫu tự viết, không phải của người thật
const CV = `Kỹ năng: Excel, SQL, Power BI, Python, tiếng Anh giao tiếp, làm việc nhóm, thuyết trình.
Kinh nghiệm: thực tập sinh phân tích dữ liệu bán hàng 6 tháng, làm báo cáo tuần bằng Excel và Power BI.`;

// chấm chạm và vệt vuốt, vẽ đè lên trang (không bắt sự kiện)
const TOUCH_JS = () => {
  const css = `.__t{position:fixed;z-index:99999;pointer-events:none;width:44px;height:44px;margin:-22px 0 0 -22px;border-radius:50%;
    background:rgb(30 30 30 / .28);border:2px solid rgb(255 255 255 / .9);box-shadow:0 0 0 1px rgb(0 0 0 / .25);transition:transform .35s,opacity .35s}`;
  addEventListener('DOMContentLoaded', () => document.head.append(Object.assign(document.createElement('style'), { textContent: css })));
  const dot = (x, y) => { const d = Object.assign(document.createElement('div'), { className: '__t' });
    d.style.left = x + 'px'; d.style.top = y + 'px'; document.body.append(d); return d; };
  window.__tap = (x, y) => { const d = dot(x, y); d.style.transform = 'scale(.6)';
    requestAnimationFrame(() => { d.style.transform = 'scale(1)'; });
    setTimeout(() => { d.style.opacity = '0'; d.style.transform = 'scale(1.5)'; }, 450); setTimeout(() => d.remove(), 900); };
  window.__swipe = (x, y, dy) => { const d = dot(x, y); d.style.transition = 'top .6s ease-out, opacity .3s';
    requestAnimationFrame(() => { d.style.top = (y - dy) + 'px'; });
    setTimeout(() => { d.style.opacity = '0'; }, 600); setTimeout(() => d.remove(), 950); };
};

rmSync(OUT, { recursive: true, force: true }); mkdirSync(OUT, { recursive: true });
// shortcut: video Playwright chỉ đúng cỡ khung (390×664), không nét hơn được; cần bản nét thì chạy HEADED=1 và quay màn hình máy Mac
const browser = await chromium.launch({ headless: !process.env.HEADED });
const phone = devices['iPhone 13'];
const ctx = await browser.newContext({ ...phone, recordVideo: { dir: OUT, size: phone.viewport } });
await ctx.addInitScript(TOUCH_JS);
const page = await ctx.newPage();
const wait = ms => page.waitForTimeout(ms);
const { width: W, height: H } = phone.viewport;

async function tap(loc, after = 700) {
  await loc.evaluate(el => el.scrollIntoView({ behavior: 'smooth', block: 'center' }));
  await wait(450);
  const b = await loc.boundingBox();
  await page.evaluate(([x, y]) => window.__tap(x, y), [b.x + b.width / 2, b.y + b.height / 2]);
  await wait(250);
  await loc.tap();
  await wait(after);
}
async function swipe(dy, after = 900) {
  await page.evaluate(([x, y, dy]) => { window.__swipe(x, y, dy); window.scrollBy({ top: dy, behavior: 'smooth' }); }, [W * 0.7, H * 0.7, dy]);
  await wait(after);
}
const swipes = async (n, dy = 420, after = 1100) => { for (let i = 0; i < n; i++) await swipe(dy, after); };

// bắt đầu từ hồ sơ trống
await page.goto(`${BASE}/huong-nghiep/#/`);
await page.evaluate(() => localStorage.clear());
await page.reload();
await page.locator('.hello h1').waitFor();
await wait(2500);

// 1. chào: nhập tên, chọn "Sinh viên", bắt đầu
const name = page.locator('.form input[type=text]');
await tap(name, 300);
await name.pressSequentially('Minh', { delay: 160 });
await wait(500);
await tap(page.locator('.pill', { hasText: 'Sinh viên' }));
await tap(page.locator('a.btn.primary.wide'), 900);

// 2. trắc nghiệm 24 câu: vài câu đầu chậm để người xem đọc, sau đó nhanh dần
for (const [i, [type]] of copy.quiz.items.entries()) {
  await page.locator('.qcard h2').waitFor();
  await wait(i < 3 ? 1400 : 350);
  await tap(page.locator('.opt').nth(LIKE[type]), 150);
}

// 3. kết quả: mã Holland, rồi các nhóm nghề hợp nhất
await page.locator('.me').waitFor();
await wait(2500);
await swipes(3);
await tap(page.locator('.jcs .jc').first(), 1500);

// 4. nhóm nghề → nghề cụ thể (nhóm chưa tách nghề thì đã ở trang nghề)
if (await page.locator('.tabs').count() === 0) {
  await swipes(1);
  await tap(page.locator('.jcs .jc').first(), 1500);
}

// 5. trang nghề: tổng quan, thị trường, kiểm tra độ hợp
const tab = i => page.locator('.tabs a').nth(i);
await tap(tab(0), 1500);
await swipes(4);
await page.evaluate(() => scrollTo({ top: 0, behavior: 'smooth' })); await wait(800);
await tap(tab(1), 1500);
await swipes(2);
// chọn kỹ năng đầu bảng để mở biểu đồ 12 tháng
await tap(page.locator('.skillbars tr.pickable').first(), 2500);
await swipes(4);
await page.evaluate(() => scrollTo({ top: 0, behavior: 'smooth' })); await wait(800);
await tap(tab(2), 1500);
for (let i = 0; i < 3; i++) await tap(page.locator('.pick .skill:not(.on)').first(), 900);
await wait(800);

// 6. dán CV và quét
await tap(page.locator('.paste summary'), 600);
const box = page.locator('.paste textarea');
await tap(box, 300);
await box.pressSequentially(CV, { delay: 18 });
await wait(600);
await tap(page.locator('.paste button'), 1200);
await page.locator('.cvres').evaluate(el => el.scrollIntoView({ behavior: 'smooth', block: 'start' }));
await wait(1500);
await swipes(2, 300, 1500);
await wait(1500);

const video = page.video();
await ctx.close();
await video.saveAs(`${OUT}demo-huong-nghiep.webm`);
await video.delete();
await browser.close();
console.log(`Đã lưu ${OUT}demo-huong-nghiep.webm`);
// đổi sang mp4 (H.264) nếu máy có ffmpeg
const mp4 = spawnSync('ffmpeg', ['-y', '-loglevel', 'error', '-i', `${OUT}demo-huong-nghiep.webm`, '-c:v', 'libx264', '-crf', '18',
  '-preset', 'slow', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', `${OUT}demo-huong-nghiep.mp4`], { stdio: 'inherit' });
console.log(mp4.status === 0 ? `Đã lưu ${OUT}demo-huong-nghiep.mp4` : 'Không đổi được sang mp4 (cần cài ffmpeg).');
