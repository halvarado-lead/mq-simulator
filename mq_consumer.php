<?php
// Simple PHP consumer for IBM MQ using the mqseries extension (PECL)

$queueManager = getenv('MQ_QMGR_NAME') ?: 'AUTORIZA';
$channel      = getenv('MQ_CHANNEL')    ?: 'DEV.APP.SVRCONN';
$host         = getenv('MQ_HOST')       ?: 'ibmmq';
$port         = getenv('MQ_PORT')       ?: '1414';
$queueName    = getenv('MQ_QUEUE')      ?: 'BOFTD_ENV';
$user         = getenv('MQ_USER')       ?: 'app';
$password     = getenv('MQ_PASSWORD')   ?: 'passw0rd';

$connName = $host . '(' . $port . ')';

// Build Client Channel Definition (CD)
$cd = [
    'ChannelName'    => $channel,
    'ConnectionName' => $connName,
    'TransportType'  => MQSERIES_MQXPT_TCP,
];

// Security parms for userid/password
$sp = [
    'UserId'   => $user,
    'Password' => $password,
];

// Connection options (CNO) with client connection and security parms
$cno = [
    'Options'       => MQSERIES_MQCNO_HANDLE_SHARE_NO_BLOCK,
    'ClientConn'    => $cd,
    'SecurityParms' => $sp,
];

$hConn = null; $compCode = 0; $reason = 0;
mqseries_connx($queueManager, $cno, $hConn, $compCode, $reason);
if ($compCode !== MQSERIES_MQCC_OK) {
    fwrite(STDERR, "MQ CONNX failed: CC=$compCode RC=$reason\n");
    exit(1);
}
fwrite(STDOUT, "Connected to MQ $queueManager via $channel @ $connName\n");

// Open queue for input
$od = [ 'ObjectName' => $queueName, 'ObjectQMgrName' => $queueManager ];
$openOpts = MQSERIES_MQOO_INPUT_AS_Q_DEF | MQSERIES_MQOO_FAIL_IF_QUIESCING;
$hObj = null; $compCode = 0; $reason = 0;
mqseries_open($hConn, $od, $openOpts, $hObj, $compCode, $reason);
if ($compCode !== MQSERIES_MQCC_OK) {
    fwrite(STDERR, "MQ OPEN failed: CC=$compCode RC=$reason\n");
    mqseries_disc($hConn, $compCode, $reason);
    exit(1);
}
fwrite(STDOUT, "Opened queue '$queueName' for reading\n");

// Get message options: wait up to 2 seconds, convert to local codepage
$md  = [];
$gmo = [
    'Options'      => MQSERIES_MQGMO_WAIT | MQSERIES_MQGMO_NO_SYNCPOINT | MQSERIES_MQGMO_CONVERT | MQSERIES_MQGMO_FAIL_IF_QUIESCING,
    'WaitInterval' => 2000,
];

// Read loop
while (true) {
    $bufferLen = 1024 * 1024; // 1 MB
    $msg = '';
    $dataLen = 0;
    $compCode = 0; $reason = 0;
    mqseries_get($hConn, $hObj, $md, $gmo, $bufferLen, $msg, $dataLen, $compCode, $reason);

    if ($compCode === MQSERIES_MQCC_FAILED && $reason === MQSERIES_MQRC_NO_MSG_AVAILABLE) {
        // Timeout waiting for message
        continue;
    }
    if ($compCode !== MQSERIES_MQCC_OK) {
        fwrite(STDERR, "MQ GET failed: CC=$compCode RC=$reason\n");
        break;
    }

    // Try JSON decode for nicer output
    $text = $msg; // already converted
    $decoded = json_decode($text, true);
    if (json_last_error() === JSON_ERROR_NONE) {
        if (is_array($decoded) && array_key_exists('id_lote', $decoded)) {
            echo "Recibido id_lote=" . $decoded['id_lote'] . "\n";
        } else {
            echo "Recibido JSON: " . json_encode($decoded) . "\n";
        }
    } else {
        echo "Recibido (texto): $text\n";
    }
}

// Cleanup
mqseries_close($hConn, $hObj, MQSERIES_MQCO_NONE, $compCode, $reason);
mqseries_disc($hConn, $compCode, $reason);
?>

