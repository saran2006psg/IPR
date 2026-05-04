import { jsPDF } from 'jspdf';
import autoTable from 'jspdf-autotable';

const PAGE = {
  width: 210,
  height: 297,
  margin: 16,
};

const COLORS = {
  title: [17, 24, 39],
  text: [55, 65, 81],
  muted: [107, 114, 128],
  border: [229, 231, 235],
  high: [220, 38, 38],
  medium: [217, 119, 6],
  low: [5, 150, 105],
  white: [255, 255, 255],
};

function sanitizeFilePart(value) {
  return String(value || '')
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
    .slice(0, 40);
}

function formatDateTime(value) {
  try {
    return new Date(value).toLocaleString();
  } catch {
    return String(value || 'N/A');
  }
}

function riskColor(level) {
  switch (level) {
    case 'HIGH':
      return COLORS.high;
    case 'MEDIUM':
      return COLORS.medium;
    case 'LOW':
      return COLORS.low;
    default:
      return COLORS.muted;
  }
}

function normalizeRisk(level) {
  if (level === 'HIGH' || level === 'MEDIUM' || level === 'LOW') {
    return level;
  }
  return 'UNKNOWN';
}

function buildSummary(results) {
  const summary = {
    HIGH: 0,
    MEDIUM: 0,
    LOW: 0,
    UNKNOWN: 0,
  };

  for (const row of results) {
    summary[normalizeRisk(row?.risk_level)] += 1;
  }

  const total = Math.max(1, results.length);
  const weightedRiskScore = Math.round(
    ((summary.HIGH * 100) + (summary.MEDIUM * 60) + (summary.LOW * 20)) / total
  );

  return {
    ...summary,
    weightedRiskScore,
  };
}

function drawReportHeader(doc, agreementType, userType, generatedAt, summary, clauseCount) {
  const left = PAGE.margin;
  const width = PAGE.width - PAGE.margin * 2;

  doc.setFillColor(248, 250, 252);
  doc.roundedRect(left, 12, width, 34, 2, 2, 'F');
  doc.setDrawColor(...COLORS.border);
  doc.roundedRect(left, 12, width, 34, 2, 2, 'S');

  doc.setTextColor(...COLORS.title);
  doc.setFont('helvetica', 'bold');
  doc.setFontSize(16);
  doc.text('Contract Risk Analysis Report', left + 4, 22);

  doc.setFont('helvetica', 'normal');
  doc.setTextColor(...COLORS.text);
  doc.setFontSize(10);
  doc.text(`Agreement Type: ${agreementType || 'N/A'}`, left + 4, 29);
  doc.text(`Perspective: ${userType || 'N/A'}`, left + 4, 34);
  doc.text(`Generated: ${formatDateTime(generatedAt)}`, left + 4, 39);

  const scoreX = left + width - 46;
  doc.setDrawColor(...COLORS.border);
  doc.roundedRect(scoreX, 17, 40, 24, 2, 2, 'S');
  doc.setFont('helvetica', 'bold');
  doc.setFontSize(9);
  doc.setTextColor(...COLORS.muted);
  doc.text('Risk Score', scoreX + 6, 24);

  doc.setFontSize(18);
  doc.setTextColor(...riskColor(summary.weightedRiskScore >= 70 ? 'HIGH' : summary.weightedRiskScore >= 40 ? 'MEDIUM' : 'LOW'));
  doc.text(String(summary.weightedRiskScore), scoreX + 13, 34);

  doc.setFont('helvetica', 'normal');
  doc.setFontSize(9);
  doc.setTextColor(...COLORS.text);
  doc.text(`Total clauses: ${clauseCount}`, scoreX + 6, 39);

  const y = 53;
  const cardW = (width - 8) / 3;
  const cards = [
    { label: 'High Risk', value: summary.HIGH, color: COLORS.high, bg: [254, 242, 242] },
    { label: 'Medium Risk', value: summary.MEDIUM, color: COLORS.medium, bg: [255, 251, 235] },
    { label: 'Low Risk', value: summary.LOW, color: COLORS.low, bg: [236, 253, 245] },
  ];

  cards.forEach((card, idx) => {
    const x = left + idx * (cardW + 4);
    doc.setFillColor(...card.bg);
    doc.roundedRect(x, y, cardW, 18, 2, 2, 'F');
    doc.setDrawColor(...COLORS.border);
    doc.roundedRect(x, y, cardW, 18, 2, 2, 'S');
    doc.setFont('helvetica', 'bold');
    doc.setFontSize(11);
    doc.setTextColor(...card.color);
    doc.text(String(card.value), x + 4, y + 7);
    doc.setFont('helvetica', 'normal');
    doc.setFontSize(9);
    doc.text(card.label, x + 4, y + 13);
  });

  doc.setDrawColor(...COLORS.border);
  doc.line(left, y + 24, left + width, y + 24);
}

function addClauseTable(doc, results) {
  autoTable(doc, {
    startY: 83,
    margin: { left: PAGE.margin, right: PAGE.margin },
    head: [['#', 'Risk', 'Clause Summary', 'Rationale']],
    body: results.map((row, idx) => {
      const clause = String(row?.clause || '').replace(/\s+/g, ' ').trim();
      const explanation = String(row?.explanation || '').replace(/\s+/g, ' ').trim();
      return [
        String(idx + 1),
        normalizeRisk(row?.risk_level),
        clause.slice(0, 180) + (clause.length > 180 ? '...' : ''),
        explanation.slice(0, 170) + (explanation.length > 170 ? '...' : ''),
      ];
    }),
    styles: {
      font: 'helvetica',
      fontSize: 9,
      textColor: COLORS.text,
      lineColor: COLORS.border,
      lineWidth: 0.2,
      cellPadding: 2,
      valign: 'top',
      overflow: 'linebreak',
    },
    headStyles: {
      fillColor: [15, 23, 42],
      textColor: COLORS.white,
      fontStyle: 'bold',
    },
    columnStyles: {
      0: { cellWidth: 10, halign: 'center' },
      1: { cellWidth: 20, halign: 'center' },
      2: { cellWidth: 74 },
      3: { cellWidth: 74 },
    },
    didParseCell: (hook) => {
      if (hook.section !== 'body' || hook.column.index !== 1) {
        return;
      }

      const risk = String(hook.cell.raw || 'UNKNOWN');
      hook.cell.styles.textColor = riskColor(risk);
      hook.cell.styles.fontStyle = 'bold';
    },
  });
}

function addClauseDetailPages(doc, results) {
  for (let idx = 0; idx < results.length; idx += 1) {
    const row = results[idx] || {};
    const risk = normalizeRisk(row.risk_level);

    doc.addPage();

    const left = PAGE.margin;
    const width = PAGE.width - PAGE.margin * 2;

    doc.setTextColor(...COLORS.title);
    doc.setFont('helvetica', 'bold');
    doc.setFontSize(14);
    doc.text(`Clause ${idx + 1} - Detailed Review`, left, 18);

    const riskFill = risk === 'HIGH' ? [254, 242, 242] : risk === 'MEDIUM' ? [255, 251, 235] : [236, 253, 245];
    doc.setFillColor(...riskFill);
    doc.setDrawColor(...COLORS.border);
    doc.roundedRect(left, 24, width, 12, 2, 2, 'S');
    doc.setFontSize(10);
    doc.setTextColor(...riskColor(risk));
    doc.text(`Risk Level: ${risk}`, left + 3, 31.5);

    doc.setTextColor(...COLORS.title);
    doc.setFontSize(11);
    doc.text('Clause Text', left, 45);

    doc.setFont('helvetica', 'normal');
    doc.setTextColor(...COLORS.text);
    doc.setFontSize(10);
    const clauseLines = doc.splitTextToSize(String(row.clause || 'N/A'), width);
    doc.text(clauseLines, left, 51);

    let nextY = 51 + clauseLines.length * 4.4 + 8;
    if (nextY > 260) {
      doc.addPage();
      nextY = 20;
    }

    doc.setFont('helvetica', 'bold');
    doc.setFontSize(11);
    doc.setTextColor(...COLORS.title);
    doc.text('Risk Explanation', left, nextY);

    doc.setFont('helvetica', 'normal');
    doc.setFontSize(10);
    doc.setTextColor(...COLORS.text);
    const explanationLines = doc.splitTextToSize(String(row.explanation || 'No explanation provided.'), width);
    doc.text(explanationLines, left, nextY + 6);

    nextY = nextY + 6 + explanationLines.length * 4.4 + 8;
    if (nextY <= 250 && Array.isArray(row.similar_clauses) && row.similar_clauses.length > 0) {
      doc.setFont('helvetica', 'bold');
      doc.setFontSize(11);
      doc.setTextColor(...COLORS.title);
      doc.text('Precedence Matches', left, nextY);

      const matches = row.similar_clauses.slice(0, 3).map((item, i) => {
        const source = item?.document || item?.clause_type || `Match ${i + 1}`;
        const text = String(item?.text || '').replace(/\s+/g, ' ').trim();
        return `${source}: ${text}`;
      });

      doc.setFont('helvetica', 'normal');
      doc.setFontSize(9);
      doc.setTextColor(...COLORS.text);
      const matchLines = doc.splitTextToSize(matches.join('\n'), width);
      doc.text(matchLines, left, nextY + 6);
    }
  }
}

function addPageFooters(doc) {
  const pageCount = doc.getNumberOfPages();
  for (let page = 1; page <= pageCount; page += 1) {
    doc.setPage(page);
    doc.setFont('helvetica', 'normal');
    doc.setFontSize(8);
    doc.setTextColor(...COLORS.muted);
    doc.text(`Page ${page} of ${pageCount}`, PAGE.width - PAGE.margin - 24, PAGE.height - 8);
  }
}

export function exportAnalysisReportPdf({ results, agreementType, userType, generatedAt = new Date() }) {
  if (!Array.isArray(results) || results.length === 0) {
    throw new Error('No analysis results available to export.');
  }

  const summary = buildSummary(results);
  const doc = new jsPDF({ orientation: 'portrait', unit: 'mm', format: 'a4' });

  drawReportHeader(doc, agreementType, userType, generatedAt, summary, results.length);
  addClauseTable(doc, results);
  addClauseDetailPages(doc, results);
  addPageFooters(doc);

  const datePart = new Date(generatedAt).toISOString().slice(0, 10);
  const agreementPart = sanitizeFilePart(agreementType || 'agreement');
  const fileName = `risk-analysis-report-${agreementPart}-${datePart}.pdf`;

  doc.save(fileName);
}
