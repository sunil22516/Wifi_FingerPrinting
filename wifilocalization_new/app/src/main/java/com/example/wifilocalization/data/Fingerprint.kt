//package com.example.wifilocalization.data
//
//data class Fingerprint(
//    val location: String,
//    val rssiValues: List<Int>
//)

//Try2
//package com.example.wifilocalization.data
//
//data class Fingerprint(
//    val location: String,
//    val wifiMap: Map<String, Int> // BSSID → RSSI
//)

//TRY3
//package com.example.wifilocalization.data
//
//data class Fingerprint(
//    val location: String,
//    val wifiMap: Map<String, Int>,
//    val timestamp: String
//)

package com.example.wifilocalization.data

data class Fingerprint(
    val location: String,
    val wifiMap: Map<String, Int>,
    val timestamp: String
)