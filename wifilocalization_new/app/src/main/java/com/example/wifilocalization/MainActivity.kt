////package com.example.wifilocalization
////
////import android.Manifest
////import android.os.Bundle
////import androidx.activity.ComponentActivity
////import androidx.activity.compose.setContent
////import androidx.compose.foundation.layout.Column
////import androidx.compose.material3.*
////import androidx.compose.runtime.*
////import androidx.core.app.ActivityCompat
////import com.example.wifilocalization.data.Fingerprint
////import com.example.wifilocalization.data.FingerprintDatabase
////import com.example.wifilocalization.knn.KNNClassifier
////import com.example.wifilocalization.wifi.WifiScanner
////
////import androidx.compose.foundation.layout.*
////import androidx.compose.ui.Alignment
////import androidx.compose.ui.Modifier
////import androidx.compose.ui.unit.dp
////
////class MainActivity : ComponentActivity() {
////
////    override fun onCreate(savedInstanceState: Bundle?) {
////        super.onCreate(savedInstanceState)
////
////        ActivityCompat.requestPermissions(
////            this,
////            arrayOf(Manifest.permission.ACCESS_FINE_LOCATION),
////            1
////        )
////
////        val scanner = WifiScanner(this)
////        val knn = KNNClassifier()
////
////        setContent {
////
////            var locationName by remember { mutableStateOf("") }
////            var result by remember { mutableStateOf("No prediction yet") }
////            var rssiText by remember { mutableStateOf("RSSI will appear here") }
////
////            MaterialTheme {
////
////                Column(
////                    modifier = Modifier
////                        .fillMaxSize()
////                        .padding(16.dp),
////                    verticalArrangement = Arrangement.Center,
////                    horizontalAlignment = Alignment.CenterHorizontally
////                ) {
////
////                    TextField(
////                        value = locationName,
////                        onValueChange = { locationName = it },
////                        label = { Text("Enter Location Name") }
////                    )
////
////                    Spacer(modifier = Modifier.height(16.dp))
////
////                    // 🔵 TRAIN BUTTON
////                    Button(onClick = {
////
////                        val rssi = scanner.scan()
////
////                        if (rssi.isEmpty()) {
////                            result = "❌ Scan failed (Turn ON Location & WiFi)"
////                            return@Button
////                        }
////
////                        rssiText = "Train RSSI: ${rssi.joinToString()}"
////
////                        FingerprintDatabase.add(
////                            Fingerprint(locationName, rssi)
////                        )
////
////                        result = "✅ Saved: $locationName"
////
////                    }) {
////                        Text("Train Location")
////                    }
////
////                    Spacer(modifier = Modifier.height(12.dp))
////
////                    // 🟢 PREDICT BUTTON
////                    Button(onClick = {
////
////                        val current = scanner.scan()
////
////                        if (current.isEmpty()) {
////                            result = "❌ Scan failed"
////                            return@Button
////                        }
////
////                        rssiText = "Current RSSI: ${current.joinToString()}"
////
////                        val predicted = knn.predict(
////                            current,
////                            FingerprintDatabase.getAll()
////                        )
////
////                        result = "📍 Predicted: $predicted"
////
////                    }) {
////                        Text("Predict Location")
////                    }
////
////                    Spacer(modifier = Modifier.height(16.dp))
////
////                    Text(result)
////
////                    Spacer(modifier = Modifier.height(8.dp))
////
////                    Text(rssiText)
////                }
////
////
////            }
////        }
////    }
////}
//
//
////TRY3
//package com.example.wifilocalization
//
//import android.Manifest
//import android.os.Bundle
//import androidx.activity.ComponentActivity
//import androidx.activity.compose.setContent
//import androidx.compose.foundation.layout.*
//import androidx.compose.material3.*
//import androidx.compose.runtime.*
//import androidx.core.app.ActivityCompat
//import androidx.compose.ui.Alignment
//import androidx.compose.ui.Modifier
//import androidx.compose.ui.unit.dp
//
//import com.example.wifilocalization.data.Fingerprint
//import com.example.wifilocalization.data.FingerprintDatabase
//import com.example.wifilocalization.knn.KNNClassifier
//import com.example.wifilocalization.wifi.WifiScanner
//
//import java.text.SimpleDateFormat
//import java.util.Date
//import java.util.Locale
//import android.util.Log
//
//
//class MainActivity : ComponentActivity() {
//
//    override fun onCreate(savedInstanceState: Bundle?) {
//        super.onCreate(savedInstanceState)
//
//        // Request permission
////        ActivityCompat.requestPermissions(
////            this,
////            arrayOf(Manifest.permission.ACCESS_FINE_LOCATION),
////            1
////        )
//        ActivityCompat.requestPermissions(
//            this,
//            arrayOf(
//                Manifest.permission.ACCESS_FINE_LOCATION,
//                Manifest.permission.ACCESS_COARSE_LOCATION,
//                Manifest.permission.NEARBY_WIFI_DEVICES   // 🔥 ADD THIS
//            ),
//            1
//        )
//
//        val scanner = WifiScanner(this)
//        val knn = KNNClassifier()
//
//        setContent {
//
//            var locationName by remember { mutableStateOf("") }
//            var result by remember { mutableStateOf("No prediction yet") }
//            var rssiText by remember { mutableStateOf("WiFi data will appear here") }
//            var isScanning by remember { mutableStateOf(false) }
//
//            // 👇 HERE
////            LaunchedEffect(isScanning) {
////                while (isScanning) {
////                    result = "Loop running..."
////
////                    val wifiMap = scanner.scan()
////
////                    if (wifiMap.isNotEmpty()) {
////                        rssiText = "Live Data:\n" +
////                                wifiMap.entries.joinToString("\n") {
////                                    "${it.key.takeLast(5)} → ${it.value}"
////                                }
////                    } else {
////                        rssiText = "❌ No WiFi data"
////                    }
////
////                    kotlinx.coroutines.delay(2000)
////                }
////            }
//
//
////            LaunchedEffect(isScanning) {
////                val formatter = SimpleDateFormat("HH:mm:ss", Locale.getDefault())
////
////                while (isScanning) {
////
////                    val time = formatter.format(Date()) // 🔥 current time
////
////                    val wifiMap = scanner.scan()
////
////                    if (wifiMap.isNotEmpty()) {
////                        rssiText = "[$time]\n" +
////                                wifiMap.entries.joinToString("\n") {
////                                    "${it.key.takeLast(5)} → ${it.value}"
////                                }
////                    } else {
////                        rssiText = "[$time]\n❌ No WiFi data"
////                    }
////
////                    kotlinx.coroutines.delay(2000)
////                }
////            }
//
//            LaunchedEffect(isScanning) {
//
//                val formatter = SimpleDateFormat("HH:mm:ss", Locale.getDefault())
//
//                while (isScanning) {
//
//                    val time = formatter.format(Date())
//
//                    val wifiMap = scanner.scan()
//
//                    if (wifiMap.isNotEmpty()) {
//
//                        val logData = wifiMap.entries.joinToString(" | ") {
//                            "${it.key.takeLast(5)}:${it.value}"
//                        }
//
//                        // 🔥 LOGCAT OUTPUT
//                        Log.d("WIFI_DEBUG", "[$time] $logData")
//
//                        rssiText = "[$time]\n" +
//                                wifiMap.entries.joinToString("\n") {
//                                    "${it.key.takeLast(5)} → ${it.value}"
//                                }
//
//                    } else {
//
//                        Log.e("WIFI_DEBUG", "[$time] ❌ No WiFi data")
//
//                        rssiText = "[$time]\n❌ No WiFi data"
//                    }
//
//                    kotlinx.coroutines.delay(2000)
//                }
//            }
//
//            MaterialTheme {
//
//                Column(
//                    modifier = Modifier
//                        .fillMaxSize()
//                        .padding(16.dp),
//                    verticalArrangement = Arrangement.Center,
//                    horizontalAlignment = Alignment.CenterHorizontally
//                ) {
//
//                    // 📍 Location Input
//                    TextField(
//                        value = locationName,
//                        onValueChange = { locationName = it },
//                        label = { Text("Enter Location Name") }
//                    )
//
//                    Spacer(modifier = Modifier.height(16.dp))
//
//                    // 🔵 TRAIN BUTTON
//                    Button(onClick = {
//
//                        val wifiMap = scanner.scan()
//
//                        if (wifiMap.isEmpty()) {
//                            result = "❌ Scan failed (Turn ON WiFi & Location)"
//                            return@Button
//                        }
//
//                        // Show WiFi data
//                        rssiText = "Train Data:\n" +
//                                wifiMap.entries.joinToString("\n") {
//                                    "${it.key.takeLast(5)} → ${it.value}"
//                                }
//
//                        // Save fingerprint
//                        FingerprintDatabase.add(
//                            Fingerprint(locationName, wifiMap)
//                        )
//
//                        result = "✅ Saved: $locationName"
//
//                    }) {
//                        Text("Train Location")
//                    }
//
//                    Spacer(modifier = Modifier.height(12.dp))
//
//                    // 🟢 PREDICT BUTTON
//                    Button(onClick = {
//
//                        val current = scanner.scan()
//
//                        if (current.isEmpty()) {
//                            result = "❌ Scan failed"
//                            return@Button
//                        }
//
//                        // Show current WiFi data
//                        rssiText = "Current Data:\n" +
//                                current.entries.joinToString("\n") {
//                                    "${it.key.takeLast(5)} → ${it.value}"
//                                }
//
//                        val predicted = knn.predict(
//                            current,
//                            FingerprintDatabase.getAll()
//                        )
//
//                        result = "📍 Predicted: $predicted"
//
//                    }) {
//                        Text("Predict Location")
//                    }
//                    // Live Scan
//                    Button(
//                        onClick = {
//                            isScanning = !isScanning
//                        },
//                        modifier = Modifier.fillMaxWidth()
//                    ) {
//                        Text(
//                            text = if (isScanning) "Stop Live Scan" else "Start Live Scan",
//                            modifier = Modifier.align(Alignment.CenterVertically)
//                        )
//                    }
//
//                    Spacer(modifier = Modifier.height(16.dp))
//
//                    // 🔸 Result
//                    Text(result)
//
//                    Spacer(modifier = Modifier.height(8.dp))
//
//                    // 🔸 RSSI Display
//                    Text(rssiText)
//                }
//            }
//
//
//
//
//
//        }
//    }
//}

//
//
//package com.example.wifilocalization
//
//import com.example.wifilocalization.data.FileStorage
//import android.Manifest
//import android.os.Bundle
//import android.util.Log
//import androidx.activity.ComponentActivity
//import androidx.activity.compose.setContent
//import androidx.compose.foundation.layout.*
//import androidx.compose.material3.*
//import androidx.compose.runtime.*
//import androidx.compose.ui.Alignment
//import androidx.compose.ui.Modifier
//import androidx.compose.ui.unit.dp
//import androidx.core.app.ActivityCompat
//
//import com.example.wifilocalization.data.Fingerprint
//import com.example.wifilocalization.data.FingerprintDatabase
//import com.example.wifilocalization.knn.KNNClassifier
//import com.example.wifilocalization.wifi.WifiScanner
//
//import kotlinx.coroutines.delay
//import java.text.SimpleDateFormat
//import java.util.*
//
//class MainActivity : ComponentActivity() {
//
//    override fun onCreate(savedInstanceState: Bundle?) {
//        super.onCreate(savedInstanceState)
//
//        // Request required permissions
//        ActivityCompat.requestPermissions(
//            this,
//            arrayOf(
//                Manifest.permission.ACCESS_FINE_LOCATION,
//                Manifest.permission.ACCESS_COARSE_LOCATION,
//                Manifest.permission.NEARBY_WIFI_DEVICES
//            ),
//            1
//        )
//
//        val scanner = WifiScanner(this)
//        val knn = KNNClassifier()
//        // Load saved fingerprints
//        val stored = FileStorage.loadFingerprints(this)
//
//        stored.forEach {
//            FingerprintDatabase.add(it)
//        }
//
//        setContent {
//
//            var locationName by remember { mutableStateOf("") }
//            var result by remember { mutableStateOf("No prediction yet") }
//            var rssiText by remember { mutableStateOf("WiFi data will appear here") }
//            var isScanning by remember { mutableStateOf(false) }
//
//            // Live scanning loop
//            LaunchedEffect(isScanning) {
//
////                val formatter = SimpleDateFormat("HH:mm:ss", Locale.getDefault())
//                val formatter = SimpleDateFormat("yyyy-MM-dd HH:mm:ss", Locale.getDefault())
//                val time = formatter.format(Date())
//
//                val fp = Fingerprint(locationName, wifiMap, timestamp = )
//
//                FingerprintDatabase.add(fp)
//
//                FileStorage.saveFingerprint(this@MainActivity, fp)
//
//                while (isScanning) {
//
//                    val time = formatter.format(Date())
//                    val wifiMap = scanner.scan()
//
//                    if (wifiMap.isNotEmpty()) {
//
//                        val logData = wifiMap.entries.joinToString(" | ") {
//                            "${it.key.takeLast(5)}:${it.value}"
//                        }
//
//                        Log.d("WIFI_DEBUG", "[$time] $logData")
//
//                        rssiText = "[$time]\n" +
//                                wifiMap.entries.joinToString("\n") {
//                                    "${it.key.takeLast(5)} → ${it.value}"
//                                }
//
//                    } else {
//
//                        Log.e("WIFI_DEBUG", "[$time] No WiFi detected")
//                        rssiText = "[$time]\n❌ No WiFi data"
//                    }
//
//                    delay(3000) // scan every 3 seconds
//                }
//            }
//
//            MaterialTheme {
//
//                Column(
//                    modifier = Modifier
//                        .fillMaxSize()
//                        .padding(20.dp),
//                    verticalArrangement = Arrangement.Center,
//                    horizontalAlignment = Alignment.CenterHorizontally
//                ) {
//
//                    TextField(
//                        value = locationName,
//                        onValueChange = { locationName = it },
//                        label = { Text("Enter Location Name") }
//                    )
//
//                    Spacer(modifier = Modifier.height(16.dp))
//
//                    // TRAIN BUTTON
//                    Button(
//                        onClick = {
//
//                            val wifiMap = scanner.scan()
//
//                            if (wifiMap.isEmpty()) {
//                                result = "❌ Scan failed (Enable WiFi + Location)"
//                                return@Button
//                            }
//
//                            rssiText = "Train Data:\n" +
//                                    wifiMap.entries.joinToString("\n") {
//                                        "${it.key.takeLast(5)} → ${it.value}"
//                                    }
//
////                            FingerprintDatabase.add(
////                                Fingerprint(locationName, wifiMap)
////                            )
//                            val formatter = SimpleDateFormat("yyyy-MM-dd HH:mm:ss", Locale.getDefault())
//                            val time = formatter.format(Date())
//                            val fp = Fingerprint(locationName, wifiMap, time)
//
//                            FingerprintDatabase.add(fp)
//
//                            FileStorage.saveFingerprint(this@MainActivity, fp)
//
//                            result = "✅ Location Saved: $locationName"
//                        },
//                        modifier = Modifier.fillMaxWidth()
//                    ) {
//                        Text("Train Location")
//                    }
//
//                    Spacer(modifier = Modifier.height(12.dp))
//
//                    // PREDICT BUTTON
//                    Button(
//                        onClick = {
//
//                            val current = scanner.scan()
//
//                            if (current.isEmpty()) {
//                                result = "❌ Scan failed"
//                                return@Button
//                            }
//
//                            rssiText = "Current Data:\n" +
//                                    current.entries.joinToString("\n") {
//                                        "${it.key.takeLast(5)} → ${it.value}"
//                                    }
//
//                            val predicted = knn.predict(
//                                current,
//                                FingerprintDatabase.getAll()
//                            )
//
//                            result = "📍 Predicted Location: $predicted"
//
//                        },
//                        modifier = Modifier.fillMaxWidth()
//                    ) {
//                        Text("Predict Location")
//                    }
//
//                    Spacer(modifier = Modifier.height(12.dp))
//
//                    // LIVE SCAN BUTTON
//                    Button(
//                        onClick = {
//                            isScanning = !isScanning
//                        },
//                        modifier = Modifier.fillMaxWidth()
//                    ) {
//                        Text(if (isScanning) "Stop Live Scan" else "Start Live Scan")
//                    }
//
//                    Spacer(modifier = Modifier.height(20.dp))
//
//                    Text(result)
//
//                    Spacer(modifier = Modifier.height(10.dp))
//
//                    Text(rssiText)
//                }
//            }
//        }
//    }
//}




package com.example.wifilocalization

import com.example.wifilocalization.data.FileStorage
import android.Manifest
import android.os.Bundle
import android.util.Log
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.core.app.ActivityCompat

import com.example.wifilocalization.data.Fingerprint
import com.example.wifilocalization.data.FingerprintDatabase
import com.example.wifilocalization.knn.KNNClassifier
import com.example.wifilocalization.wifi.WifiScanner

import kotlinx.coroutines.delay
import java.io.File
import java.text.SimpleDateFormat
import java.util.*

class MainActivity : ComponentActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        ActivityCompat.requestPermissions(
            this,
            arrayOf(
                Manifest.permission.ACCESS_FINE_LOCATION,
                Manifest.permission.ACCESS_COARSE_LOCATION,
                Manifest.permission.NEARBY_WIFI_DEVICES
            ),
            1
        )

        val scanner = WifiScanner(this)
        val knn = KNNClassifier()

        // Load stored fingerprints
        val stored = FileStorage.loadFingerprints(this)
        stored.forEach {
            FingerprintDatabase.add(it)
        }
        Log.d("DATASET", "Fingerprints loaded: ${stored.size}")
        stored.forEach {
            Log.d("DATASET", "Location in dataset: ${it.location}")
        }

        setContent {

            var locationName by remember { mutableStateOf("") }
            var result by remember { mutableStateOf("No prediction yet") }
            var rssiText by remember { mutableStateOf("WiFi data will appear here") }
            var isScanning by remember { mutableStateOf(false) }
            var livePrediction by remember { mutableStateOf("Live Location: Unknown") }

            // LIVE SCANNING LOOP
            LaunchedEffect(isScanning) {

                val formatter = SimpleDateFormat("yyyy-MM-dd HH:mm:ss", Locale.getDefault())

                while (isScanning) {

                    val time = formatter.format(Date())
                    val wifiMap = scanner.scan()

                    val predicted = knn.predict(
                        wifiMap,
                        FingerprintDatabase.getAll()
                    )

                    livePrediction = "📍 Live Location: $predicted"

                    if (wifiMap.isNotEmpty()) {

                        val logData = wifiMap.entries.joinToString(" | ") {
                            "${it.key.takeLast(5)}:${it.value}"
                        }

                        Log.d("WIFI_DEBUG", "[$time] $logData")

                        rssiText = "[$time]\n" +
                                wifiMap.entries.joinToString("\n") {
                                    "${it.key.takeLast(5)} → ${it.value}"
                                }

                    } else {

                        Log.e("WIFI_DEBUG", "[$time] No WiFi detected")
                        rssiText = "[$time]\n❌ No WiFi data"
                    }

                    delay(3000)
                }
            }

            MaterialTheme {

                Column(
                    modifier = Modifier
                        .fillMaxSize()
                        .padding(20.dp),
                    verticalArrangement = Arrangement.Center,
                    horizontalAlignment = Alignment.CenterHorizontally
                ) {

                    TextField(
                        value = locationName,
                        onValueChange = { locationName = it },
                        label = { Text("Enter Location Name") }
                    )

                    Spacer(modifier = Modifier.height(16.dp))

                    // TRAIN BUTTON
                    Button(
                        onClick = {

                            val wifiMap = scanner.scan()

                            if (wifiMap.isEmpty()) {
                                result = "❌ Scan failed (Enable WiFi + Location)"
                                return@Button
                            }

                            rssiText = "Train Data:\n" +
                                    wifiMap.entries.joinToString("\n") {
                                        "${it.key.takeLast(5)} → ${it.value}"
                                    }

                            val formatter = SimpleDateFormat("yyyy-MM-dd HH:mm:ss", Locale.getDefault())
                            val time = formatter.format(Date())

                            val fp = Fingerprint(locationName, wifiMap, time)

                            FingerprintDatabase.add(fp)
                            FileStorage.saveFingerprint(this@MainActivity, fp)

                            result = "✅ Location Saved: $locationName"

                            Log.d("FILE_SAVE", "Fingerprint saved: ${fp.location} at ${fp.timestamp}")
                        },
                        modifier = Modifier.fillMaxWidth()
                    ) {
                        Text("Train Location")
                    }

                    Spacer(modifier = Modifier.height(12.dp))

                    // PREDICT BUTTON
                    Button(
                        onClick = {

                            val current = scanner.scan()

                            if (current.isEmpty()) {
                                result = "❌ Scan failed"
                                return@Button
                            }

                            rssiText = "Current Data:\n" +
                                    current.entries.joinToString("\n") {
                                        "${it.key.takeLast(5)} → ${it.value}"
                                    }

                            val predicted = knn.predict(
                                current,
                                FingerprintDatabase.getAll()
                            )

                            result = "📍 Predicted Location: $predicted"
                        },
                        modifier = Modifier.fillMaxWidth()
                    ) {
                        Text("Predict Location")
                    }

                    Spacer(modifier = Modifier.height(12.dp))

                    // LIVE SCAN BUTTON
                    Button(
                        onClick = {
                            isScanning = !isScanning
                        },
                        modifier = Modifier.fillMaxWidth()
                    ) {
                        Text(if (isScanning) "Stop Live Scan" else "Start Live Scan")
                    }

                    Spacer(modifier = Modifier.height(20.dp))

                    Text(result)

//                    Spacer(modifier = Modifier.height(10.dp))

                    Spacer(modifier = Modifier.height(10.dp))

                    Text(
                        livePrediction,
                        style = MaterialTheme.typography.headlineSmall
                    )

                    Spacer(modifier = Modifier.height(10.dp))

                    Text(rssiText)


//                    Button(
//                        onClick = {
//                            FileStorage.deleteByLocation(this@MainActivity, locationName)
//
//                            // ALSO remove from in-memory database
//                            val remaining = FingerprintDatabase.getAll()
//                                .filterNot { it.location == locationName }
//
//                            // reset database
//                            FingerprintDatabase.getAll().toMutableList().clear()
//                            remaining.forEach { FingerprintDatabase.add(it) }
//
//                            result = "🗑️ Deleted: $locationName"
//                        },
//                        modifier = Modifier.fillMaxWidth()
//                    ) {
//                        Text("Delete Location")
//                    }
                    Button(
                        onClick = {
                            FileStorage.deleteByLocation(this@MainActivity, locationName)

                            // Clear memory
                            FingerprintDatabase.clear()

                            // Reload from file
                            FileStorage.loadFingerprints(this@MainActivity)
                                .forEach { FingerprintDatabase.add(it) }

                            result = "🗑️ Deleted: $locationName"
                        },
                        modifier = Modifier.fillMaxWidth()
                    ) {
                        Text("Delete Location")
                    }
//                    FileStorage.deleteByLocation(this@MainActivity, locationName)
//
//                    val file = File(this@MainActivity.filesDir, "fingerprints.csv")
//                    file.readLines().forEach {
//                        Log.d("AFTER_DELETE", it)
//                    }



                }
            }
        }
    }
}