package com.example.wifilocalization.wifi

import android.content.Context
import android.net.wifi.WifiManager
import android.util.Log

class WifiScanner(context: Context) {

//    private val wifiManager =
//        context.applicationContext.getSystemService(Context.WIFI_SERVICE) as WifiManager
    private val wifiManager =
        context.applicationContext.getSystemService(Context.WIFI_SERVICE) as WifiManager

//
//    // =========================
//    // TAKE 1 (Basic RSSI list)
//    // =========================
//    fun scanTake1(): List<Int> {
//        return try {
//            val results = wifiManager.scanResults
//
//            if (results.isEmpty()) {
//                Log.e("WIFI", "No scan results")
//                emptyList()
//            } else {
//                results.map { it.level }
//            }
//
//        } catch (e: Exception) {
//            Log.e("WIFI", "Scan failed: ${e.message}")
//            emptyList()
//        }
//    }

//
//    // =========================
//    // TAKE 2 (Full BSSID map)
//    // =========================
//    fun scanTake2(): Map<String, Int> {
//        return try {
//            val results = wifiManager.scanResults
//
//            if (results.isEmpty()) {
//                Log.e("WIFI", "No scan results")
//                emptyMap()
//            } else {
//                results.associate { it.BSSID to it.level }
//            }
//
//        } catch (e: Exception) {
//            Log.e("WIFI", "Scan failed: ${e.message}")
//            emptyMap()
//        }
//    }


//    // =========================
//    // TAKE 3 (Top 5 APs)
//    // =========================
//    fun scanTake3(): Map<String, Int> {
//        return try {
//            val results = wifiManager.scanResults
//
//            if (results.isEmpty()) {
//                Log.e("WIFI", "No scan results")
//                emptyMap()
//            } else {
//                results
//                    .sortedByDescending { it.level }
//                    .take(5)
//                    .associate { it.BSSID to it.level }
//            }
//
//        } catch (e: Exception) {
//            Log.e("WIFI", "Scan failed: ${e.message}")
//            emptyMap()
//        }
//    }


//    // =========================
//    // TAKE 4 (🔥 FIXED REAL SCAN)
//    // =========================
//    fun scan(): Map<String, Int> {
//        return try {
//
//            val success = wifiManager.startScan() // 🔥 trigger new scan
//
//            if (!success) {
//                Log.e("WIFI", "Scan throttled or failed")
//            }
//
//            val results = wifiManager.scanResults
//
//            if (results.isEmpty()) {
//                Log.e("WIFI", "No scan results")
//                emptyMap()
//            } else {
//                results
//                    .sortedByDescending { it.level }
//                    .take(5)
//                    .associate { it.BSSID to it.level }
//            }
//
//        } catch (e: Exception) {
//            Log.e("WIFI", "Scan failed: ${e.message}")
//            emptyMap()
//        }
//    }
//}

// Take 5
    fun scan(): Map<String, Int> {
        return try {

            val success = wifiManager.startScan()

            if (!success) {
                Log.e("WIFI", "Scan throttled or failed")
            }

            Thread.sleep(1000) // 🔥 WAIT for scan to complete

            val results = wifiManager.scanResults

            if (results.isEmpty()) {
                Log.e("WIFI", "No scan results")
                emptyMap()
            } else {
                results
                    .sortedByDescending { it.level }
                    .take(5)
                    .associate { it.BSSID to it.level }
            }

        } catch (e: Exception) {
            Log.e("WIFI", "Scan failed: ${e.message}")
            emptyMap()
        }
    }}