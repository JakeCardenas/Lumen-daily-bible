import 'package:flutter/material.dart';

import 'theme.dart';

void main() => runApp(MaterialApp(
      title: 'Lumen',
      theme: lumenTheme(),
      home: const Scaffold(body: Center(child: Text('Lumen'))),
    ));
