/// Converts a psalm reference in modern (Hebrew) numbering to Douay-Rheims (Vulgate) numbering.
/// Mirrors `psalm_hebrew_to_douay` in tool/lumen_data/versification.py.
(int, int) hebrewToDouayPsalm(int psalm, int verse) {
  if (psalm <= 9 || psalm >= 148) return (psalm, verse);
  if (psalm == 10) return (9, verse + 21);
  if (psalm <= 113) return (psalm - 1, verse);
  if (psalm == 114) return (113, verse);
  if (psalm == 115) return (113, verse + 8);
  if (psalm == 116) return verse <= 9 ? (114, verse) : (115, verse - 9);
  if (psalm <= 146) return (psalm - 1, verse);
  return verse <= 11 ? (146, verse) : (147, verse - 11);
}
