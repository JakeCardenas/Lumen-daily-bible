import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  test('licence texts are bundled', () async {
    expect(await rootBundle.loadString('assets/licenses/litcal-apache-2.0.txt'), contains('Apache License'));
    expect(await rootBundle.loadString('assets/licenses/stepbible-tvtms.txt'), contains('CC BY 4.0'));
    expect(await rootBundle.loadString('assets/licenses/literata-ofl.txt'), contains('SIL OPEN FONT LICENSE'));
  });
}
