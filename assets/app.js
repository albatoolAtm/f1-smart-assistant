// شعارات الفرق - المسارات بالنسبة لصفحات داخل مجلد dashboard
const TEAM_LOGOS = {
  ferrari:     "../assets/img/teams/ferrari.png",
  mercedes:    "../assets/img/teams/mercedes.png",
  redbull:     "../assets/img/teams/redbull.png",
  mclaren:     "../assets/img/teams/mclaren.png",
  astonmartin: "../assets/img/teams/astonmartin.png",
};

// حفظ إعدادات البروفايل (من profile.html)
function saveProfileSettings() {
  const select = document.getElementById("favorite-team-select");
  if (!select) return;

  const teamKey = select.value;
  const teamName = select.options[select.selectedIndex]?.text || "";

  localStorage.setItem("favoriteTeamKey", teamKey);
  localStorage.setItem("favoriteTeamName", teamName);

  alert("Saved! شعار الفريق بيظهر في الداشبورد 👌");
}

// تحميل شعار الفريق في الداشبورد
function loadFavoriteTeam() {
  const teamKey = localStorage.getItem("favoriteTeamKey");
  const teamName = localStorage.getItem("favoriteTeamName");

  const logoImg = document.getElementById("user-team-logo");
  const teamNameSpan = document.getElementById("favorite-team-name");

  if (!logoImg || !teamNameSpan) return;

  // اسم الفريق في النص
  if (teamName) {
    teamNameSpan.textContent = teamName;
  }

  // لو في فريق مختار وشعاره معروف
  if (teamKey && TEAM_LOGOS[teamKey]) {
    logoImg.src = TEAM_LOGOS[teamKey];
    logoImg.style.display = "block"; // نُظهر الصورة داخل الدائرة
  }
}

// تشغيل بعد تحميل الصفحة
document.addEventListener("DOMContentLoaded", () => {
  loadFavoriteTeam();

  // لو إحنا في صفحة البروفايل، رجّعي آخر اختيار
  const select = document.getElementById("favorite-team-select");
  if (select) {
    const savedKey = localStorage.getItem("favoriteTeamKey") || "";
    if (savedKey) {
      select.value = savedKey;
    }
  }
});
