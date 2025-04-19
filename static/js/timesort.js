document.addEventListener('DOMContentLoaded', () => {
  const table = document.getElementById('ngCoursesTable');
  const headers = table.querySelectorAll('thead .coursesHeader th');
  const tbody   = table.querySelector('tbody');

  // helper: pull out & normalize each cell’s “value” for sorting
  function getCellValue(row, colIndex) {
    const cell = row.children[colIndex];
    switch(colIndex) {
      case 0: // “-” column → use data-cid (always asc)
        return parseInt(row.dataset.cid);
      case 1: // Course name → string
        return cell.textContent.trim().toLowerCase();
      case 3: // SR Delta → “+12.3s”
        return parseFloat(cell.textContent) || 0;
      case 4: // PRSR → “56.7%”
        return parseFloat(cell.textContent) || 0;
      case 5: // Rank → integer
        return parseInt(cell.textContent) || 0;
      case 6: // STD → integer inside .stdNb
        return parseInt(cell.querySelector('.stdNb')?.textContent) || 0;
      case 7: // Date → parseable Date (assumes YYYY-MM-DD or similar)
        return new Date(cell.textContent);
      default:
        return '';
    }
  }

  // perform the actual sort
  function sortByColumn(colIndex, asc=true) {
    const rows = Array.from(tbody.querySelectorAll('tr'));
    rows.sort((a, b) => {
      const aVal = getCellValue(a, colIndex);
      const bVal = getCellValue(b, colIndex);
      if (aVal > bVal) return asc ?  1 : -1;
      if (aVal < bVal) return asc ? -1 :  1;
      return 0;
    });
    // re‑attach in new order
    rows.forEach(r => tbody.appendChild(r));
  }

  // wire up each header
  headers.forEach((th, idx) => {
    // skip “Time” column at index 2
    if (idx === 2) return;

    // determine default sort direction per column:
    //   idx 0 (“-”): asc
    //   idx 1 (Course): asc
    //   idx 3 (SR Delta): asc
    //   idx 4 (PRSR): desc
    //   idx 5 (Rank):  asc
    //   idx 6 (STD):   asc
    //   idx 7 (Date):  desc
    const defaultAsc = [0,1,3,5,6].includes(idx);

    th.style.cursor = 'pointer';
    th.addEventListener('click', () => sortByColumn(idx, defaultAsc));
  });
});
