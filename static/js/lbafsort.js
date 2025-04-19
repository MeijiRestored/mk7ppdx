document.addEventListener('DOMContentLoaded', () => {
  const table = document.getElementById('afLbTable');
  const headers = table.querySelectorAll('thead .lbHeader th');
  const tbody = table.querySelector('tbody');

  function getCellValue(row, colIndex) {
    const cell = row.children[colIndex];
    switch (colIndex) {
      case 0: // Player
        return cell.textContent.trim().toLowerCase();
      case 1: // Country (includes flag icon, so get text only)
        return cell.textContent.trim().toLowerCase();
      case 2: // Rank
        return parseInt(cell.textContent) || 0;
      case 3: // AF
        return parseFloat(cell.textContent) || 0;
      case 4: // Change
        return parseFloat(cell.textContent.trim().toLowerCase()) || 0;
      default:
        return '';
    }
  }

  function sortByColumn(colIndex, asc = true) {
    const rows = Array.from(tbody.querySelectorAll('tr'));
    rows.sort((a, b) => {
      const aVal = getCellValue(a, colIndex);
      const bVal = getCellValue(b, colIndex);
      if (aVal > bVal) return asc ? 1 : -1;
      if (aVal < bVal) return asc ? -1 : 1;
      return 0;
    });
    rows.forEach(row => tbody.appendChild(row));
  }

  headers.forEach((th, idx) => {
    const sortable = [0, 1, 2, 3, 4].includes(idx); // all columns are sortable
    if (!sortable) return;

    th.style.cursor = 'pointer';

    const defaultAsc = true; // all columns sorted ascending
    th.addEventListener('click', () => sortByColumn(idx, defaultAsc));
  });
});
